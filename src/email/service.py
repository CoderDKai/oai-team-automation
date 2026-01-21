# ==================== 邮箱服务模块 ====================
# 处理邮箱创建、验证码获取等功能 (支持多种邮箱系统)

import re
import time
import random
import string
import requests
from typing import Callable, TypeVar, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.config import (
    EMAIL_API_BASE,
    EMAIL_API_AUTH,
    EMAIL_ROLE,
    DEFAULT_PASSWORD,
    REQUEST_TIMEOUT,
    VERIFICATION_CODE_INTERVAL,
    VERIFICATION_CODE_MAX_RETRIES,
    PROXY_ENABLED,
    get_random_domain,
    get_proxy_dict,
    EMAIL_PROVIDER,
    GPTMAIL_API_BASE,
    GPTMAIL_API_KEY,
    GPTMAIL_PREFIX,
    GPTMAIL_DOMAINS,
    get_random_gptmail_domain,
    DOMAINMAIL_API_BASE,
    DOMAINMAIL_API_KEY,
    DOMAINMAIL_DOMAINS,
    get_random_domainmail_domain,
)
from src.core.logger import log


def create_session_with_retry():
    """创建带重试机制的 HTTP Session"""
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # 代理设置
    if PROXY_ENABLED:
        proxy_dict = get_proxy_dict()
        if proxy_dict:
            session.proxies = proxy_dict

    return session


# 全局 HTTP Session
http_session = create_session_with_retry()


# ==================== 通用轮询重试工具 ====================
T = TypeVar("T")


class PollResult:
    """轮询结果"""

    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error


def poll_with_retry(
    fetch_func: Callable[[], Optional[T]],
    check_func: Callable[[T], Optional[Any]],
    max_retries: int = None,
    interval: int = None,
    fast_retries: int = 5,
    fast_interval: int = 1,
    description: str = "轮询",
    on_progress: Callable[[float], None] = None,
    fibonacci_backoff: bool = False,
    backoff_max: int = 60,
) -> PollResult:
    """通用轮询重试函数

    Args:
        fetch_func: 获取数据的函数，返回原始数据或 None
        check_func: 检查数据的函数，返回提取的结果或 None
        max_retries: 最大重试次数
        interval: 正常轮询间隔 (秒)
        fast_retries: 快速轮询次数 (前 N 次使用快速间隔)
        fast_interval: 快速轮询间隔 (秒)
        description: 描述信息 (用于日志)
        on_progress: 进度回调函数，参数为已用时间 (秒)
        fibonacci_backoff: 是否使用斐波那契退避模式 (3, 5, 8, 13, 21, ...)
        backoff_max: 斐波那契退避最大间隔 (秒)，默认 60 秒

    Returns:
        PollResult: 轮询结果
    """
    if max_retries is None:
        max_retries = VERIFICATION_CODE_MAX_RETRIES
    if interval is None:
        interval = VERIFICATION_CODE_INTERVAL

    # 预计算斐波那契数列 (从 3, 5 开始: 3, 5, 8, 13, 21, 34, 55, ...)
    fibonacci_seq = [3, 5]
    while fibonacci_seq[-1] < backoff_max:
        fibonacci_seq.append(fibonacci_seq[-1] + fibonacci_seq[-2])

    start_time = time.time()
    progress_shown = False

    for i in range(max_retries):
        try:
            # 获取数据
            data = fetch_func()

            if data is not None:
                # 检查数据
                result = check_func(data)
                if result is not None:
                    if progress_shown:
                        log.progress_clear()
                    elapsed = time.time() - start_time
                    return PollResult(success=True, data=result)

        except Exception as e:
            if progress_shown:
                log.progress_clear()
                progress_shown = False
            log.warning(f"{description}异常: {e}")

        if i < max_retries - 1:
            if fibonacci_backoff:
                # 斐波那契退避: 3, 5, 8, 13, 21, ...，但不超过 backoff_max
                fib_index = min(i, len(fibonacci_seq) - 1)
                wait_time = min(fibonacci_seq[fib_index], backoff_max)
            else:
                # 动态间隔: 前 fast_retries 次使用快速间隔
                wait_time = fast_interval if i < fast_retries else interval

            elapsed = time.time() - start_time
            if on_progress:
                on_progress(elapsed)
            else:
                log.progress_inline(f"[等待中... {elapsed:.0f}s]")
                progress_shown = True

            time.sleep(wait_time)

    if progress_shown:
        log.progress_clear()

    elapsed = time.time() - start_time
    return PollResult(success=False, error=f"超时 ({elapsed:.0f}s)")


# ==================== GPTMail 临时邮箱服务 ====================
class GPTMailService:
    """GPTMail 临时邮箱服务"""

    def __init__(self, api_base: str = None, api_key: str = None):
        self.api_base = api_base or GPTMAIL_API_BASE
        self.api_key = api_key or GPTMAIL_API_KEY
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    def generate_email(self, prefix: str = None, domain: str = None) -> tuple[str, str]:
        """生成临时邮箱地址

        Args:
            prefix: 邮箱前缀 (可选)
            domain: 域名 (可选)

        Returns:
            tuple: (email, error) - 邮箱地址和错误信息
        """
        url = f"{self.api_base}/api/generate-email"

        try:
            if prefix or domain:
                payload = {}
                if prefix:
                    payload["prefix"] = prefix
                if domain:
                    payload["domain"] = domain
                response = http_session.post(
                    url, headers=self.headers, json=payload, timeout=REQUEST_TIMEOUT
                )
            else:
                response = http_session.get(
                    url, headers=self.headers, timeout=REQUEST_TIMEOUT
                )

            data = response.json()

            if data.get("success"):
                email = data.get("data", {}).get("email", "")
                log.success(f"GPTMail 生成邮箱: {email}")
                return email, None
            else:
                error = data.get("error", "Unknown error")
                log.error(f"GPTMail 生成邮箱失败: {error}")
                return None, error

        except Exception as e:
            log.error(f"GPTMail 生成邮箱异常: {e}")
            return None, str(e)

    def get_emails(self, email: str) -> tuple[list, str]:
        """获取邮箱的邮件列表

        Args:
            email: 邮箱地址

        Returns:
            tuple: (emails, error) - 邮件列表和错误信息
        """
        url = f"{self.api_base}/api/emails"
        params = {"email": email}

        try:
            response = http_session.get(
                url, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT
            )
            data = response.json()

            if data.get("success"):
                emails = data.get("data", {}).get("emails", [])
                return emails, None
            else:
                error = data.get("error", "Unknown error")
                return [], error

        except Exception as e:
            log.warning(f"GPTMail 获取邮件列表异常: {e}")
            return [], str(e)

    def get_email_detail(self, email_id: str) -> tuple[dict, str]:
        """获取单封邮件详情

        Args:
            email_id: 邮件ID

        Returns:
            tuple: (email_detail, error) - 邮件详情和错误信息
        """
        url = f"{self.api_base}/api/email/{email_id}"

        try:
            response = http_session.get(
                url, headers=self.headers, timeout=REQUEST_TIMEOUT
            )
            data = response.json()

            if data.get("success"):
                return data.get("data", {}), None
            else:
                error = data.get("error", "Unknown error")
                return {}, error

        except Exception as e:
            log.warning(f"GPTMail 获取邮件详情异常: {e}")
            return {}, str(e)

    def delete_email(self, email_id: str) -> tuple[bool, str]:
        """删除单封邮件

        Args:
            email_id: 邮件ID

        Returns:
            tuple: (success, error)
        """
        url = f"{self.api_base}/api/email/{email_id}"

        try:
            response = http_session.delete(
                url, headers=self.headers, timeout=REQUEST_TIMEOUT
            )
            data = response.json()

            if data.get("success"):
                return True, None
            else:
                return False, data.get("error", "Unknown error")

        except Exception as e:
            return False, str(e)

    def clear_inbox(self, email: str) -> tuple[int, str]:
        """清空邮箱

        Args:
            email: 邮箱地址

        Returns:
            tuple: (deleted_count, error)
        """
        url = f"{self.api_base}/api/emails/clear"
        params = {"email": email}

        try:
            response = http_session.delete(
                url, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT
            )
            data = response.json()

            if data.get("success"):
                count = data.get("data", {}).get("count", 0)
                return count, None
            else:
                return 0, data.get("error", "Unknown error")

        except Exception as e:
            return 0, str(e)

    def get_verification_code(
        self, email: str, max_retries: int = None, interval: int = None
    ) -> tuple[str, str, str]:
        """从邮箱获取验证码 (使用通用轮询重试)

        Args:
            email: 邮箱地址
            max_retries: 最大重试次数
            interval: 基础轮询间隔 (秒)

        Returns:
            tuple: (code, error, email_time) - 验证码、错误信息、邮件时间
        """
        log.info(f"GPTMail 等待验证码邮件: {email}", icon="email")

        # 用于存储邮件时间的闭包变量
        email_time_holder = [None]

        def fetch_emails():
            """获取邮件列表"""
            emails, error = self.get_emails(email)
            return emails if emails else None

        def check_for_code(emails):
            """检查邮件中是否有验证码"""
            for email_item in emails:
                subject = email_item.get("subject", "")
                content = email_item.get("content", "")
                email_time_holder[0] = email_item.get("created_at", "")

                # 尝试从主题中提取验证码
                code = self._extract_code(subject)
                if code:
                    return code

                # 尝试从内容中提取验证码
                code = self._extract_code(content)
                if code:
                    return code

            return None

        # 使用通用轮询函数
        result = poll_with_retry(
            fetch_func=fetch_emails,
            check_func=check_for_code,
            max_retries=max_retries,
            interval=interval,
            description="GPTMail 获取邮件",
        )

        if result.success:
            log.success(f"GPTMail 验证码获取成功: {result.data}")
            return result.data, None, email_time_holder[0]
        else:
            log.error(f"GPTMail 验证码获取失败 ({result.error})")
            return None, "未能获取验证码", None

    def _extract_code(self, text: str) -> str:
        """从文本中提取验证码 (优先匹配有上下文的验证码)

        Args:
            text: 邮件正文文本

        Returns:
            str: 提取到的验证码，或 None
        """
        if not text:
            return None

        # 优先使用带上下文的正则模式 (避免匹配邮箱地址中的数字)
        patterns_with_context = [
            r"代码为\s*(\d{6})",
            r"code is\s*(\d{6})",
            r"verification code[:\s]*(\d{6})",
            r"验证码[：:\s]*(\d{6})",
            r"Your code is[:\s]*(\d{6})",
            r"one-time code[:\s]*(\d{6})",
            r"一次性验证码[：:\s]*(\d{6})",
        ]

        for pattern in patterns_with_context:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # 备用方案: 匹配独立的6位数字 (排除邮箱地址中的数字)
        # 先移除邮箱地址，避免误匹配
        text_cleaned = re.sub(r'\S+@\S+', '', text)
        match = re.search(r'\b(\d{6})\b', text_cleaned)
        if match:
            return match.group(1)

        return None


# 全局 GPTMail 服务实例
gptmail_service = GPTMailService()


class DomainMailService:
    def __init__(self, api_base: str = None, api_key: str = None):
        self.api_base = api_base or DOMAINMAIL_API_BASE
        self.api_key = api_key or DOMAINMAIL_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def create_mailbox(self, address: str) -> tuple[dict, str]:
        url = f"{self.api_base}/mailboxes"
        payload = {"address": address}

        try:
            log.info(f"DomainMail 创建邮箱: {address}", icon="email")
            response = http_session.post(
                url, headers=self.headers, json=payload, timeout=REQUEST_TIMEOUT
            )
            data = response.json()

            if response.status_code == 201:
                log.success(f"DomainMail 邮箱创建成功: {address}")
                return data, None
            else:
                error = data.get("message", "Unknown error")
                log.error(f"DomainMail 邮箱创建失败: {error}")
                return None, error

        except Exception as e:
            log.error(f"DomainMail 邮箱创建异常: {e}")
            return None, str(e)

    def get_emails(
        self, address: str, page: int = 1, limit: int = 20, unread: bool = None
    ) -> tuple[list, str]:
        """获取邮箱的邮件列表

        Args:
            address: 邮箱地址
            page: 页码
            limit: 每页数量
            unread: 筛选未读邮件 (True=仅未读, False=仅已读, None=全部)

        Returns:
            tuple: (emails, error) - 邮件列表和错误信息
        """
        url = f"{self.api_base}/mailboxes/{address}/emails"
        params = {"page": page, "limit": limit}
        if unread is not None:
            # API 使用布尔值字符串 "true"/"false"
            params["unread"] = "true" if unread else "false"

        try:
            response = http_session.get(
                url, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT
            )

            # 检查响应内容类型和状态
            content_type = response.headers.get("Content-Type", "")
            if response.status_code != 200:
                # 尝试解析错误响应
                try:
                    data = response.json()
                    error = data.get("message", f"HTTP {response.status_code}")
                except Exception:
                    error = f"HTTP {response.status_code}: {response.text[:200]}"
                return [], error

            # 正常响应
            try:
                data = response.json()
            except Exception as json_err:
                # JSON 解析失败，打印原始响应帮助调试
                log.warning(f"JSON 解析失败: {json_err}")
                log.warning(f"原始响应 (前200字符): {response.text[:200]}")
                return [], f"JSON 解析失败: {json_err}"

            emails = data.get("data", [])
            return emails, None

        except Exception as e:
            log.warning(f"DomainMail 获取邮件列表异常: {e}")
            return [], str(e)

    def get_email_detail(self, email_id: str) -> tuple[dict, str]:
        url = f"{self.api_base}/emails/{email_id}"

        try:
            response = http_session.get(
                url, headers=self.headers, timeout=REQUEST_TIMEOUT
            )
            data = response.json()

            if response.status_code == 200:
                return data, None
            else:
                error = data.get("message", "Unknown error")
                return {}, error

        except Exception as e:
            log.warning(f"DomainMail 获取邮件详情异常: {e}")
            return {}, str(e)

    def mark_email_as_read(self, email_id: str) -> tuple[bool, str]:
        """将邮件标记为已读

        Args:
            email_id: 邮件ID

        Returns:
            tuple: (success, error) - 是否成功和错误信息
        """
        url = f"{self.api_base}/emails/{email_id}"
        payload = {"isRead": True}

        try:
            response = http_session.patch(
                url, headers=self.headers, json=payload, timeout=REQUEST_TIMEOUT
            )
            data = response.json()

            if response.status_code == 200:
                return True, None
            else:
                error = data.get("message", "Unknown error")
                return False, error

        except Exception as e:
            log.warning(f"DomainMail 标记已读异常: {e}")
            return False, str(e)

    def _extract_code_from_body(self, text: str) -> str:
        """从邮件正文中提取验证码 (优先匹配有上下文的验证码)

        Args:
            text: 邮件正文文本

        Returns:
            str: 提取到的验证码，或 None
        """
        if not text:
            return None

        # 优先使用带上下文的正则模式 (避免匹配邮箱地址中的数字)
        patterns_with_context = [
            r"代码为\s*(\d{6})",
            r"code is\s*(\d{6})",
            r"verification code[:\s]*(\d{6})",
            r"验证码[：:\s]*(\d{6})",
            r"Your code is[:\s]*(\d{6})",
            r"one-time code[:\s]*(\d{6})",
            r"一次性验证码[：:\s]*(\d{6})",
        ]

        for pattern in patterns_with_context:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # 备用方案: 匹配独立的6位数字 (排除邮箱地址中的数字)
        # 先移除邮箱地址，避免误匹配
        text_cleaned = re.sub(r'\S+@\S+', '', text)
        match = re.search(r'\b(\d{6})\b', text_cleaned)
        if match:
            return match.group(1)

        return None

    def _extract_code(self, text: str) -> str:
        """从文本中提取验证码 (兼容旧接口)"""
        return self._extract_code_from_body(text)

    def get_verification_code(
        self, address: str, max_retries: int = None, interval: int = None
    ) -> tuple[str, str, str]:
        """从邮箱获取验证码 (仅获取未读邮件，获取成功后标记为已读)

        Args:
            address: 邮箱地址
            max_retries: 最大重试次数
            interval: 轮询间隔 (秒)

        Returns:
            tuple: (code, error, email_time) - 验证码、错误信息、邮件时间
        """
        log.info(f"DomainMail 等待验证码邮件: {address}", icon="email")

        email_time_holder = [None]
        email_id_holder = [None]  # 用于存储邮件ID，便于后续标记已读

        def fetch_emails():
            # 仅获取未读邮件，避免获取到旧验证码
            emails, error = self.get_emails(address, page=1, limit=10, unread=True)
            return emails if emails else None

        def check_for_code(emails):
            for email_item in emails:
                email_id = email_item.get("id", "")
                subject = email_item.get("subject", "")
                snippet = email_item.get("snippet", "")
                email_time_holder[0] = email_item.get("receivedAt", "")

                # 从主题提取验证码 (主题一般不包含邮箱地址)
                code = self._extract_code_from_body(subject)
                if code:
                    email_id_holder[0] = email_id
                    return code

                # 从摘要提取验证码 (摘要可能包含发件人信息，需要过滤)
                code = self._extract_code_from_body(snippet)
                if code:
                    email_id_holder[0] = email_id
                    return code

                # 从邮件详情的正文提取验证码 (更准确)
                if email_id:
                    detail, error = self.get_email_detail(email_id)
                    if detail:
                        text_body = detail.get("textBody", "")
                        code = self._extract_code_from_body(text_body)
                        if code:
                            email_id_holder[0] = email_id
                            return code

            return None

        result = poll_with_retry(
            fetch_func=fetch_emails,
            check_func=check_for_code,
            max_retries=max_retries,
            interval=interval,
            description="DomainMail 获取邮件",
            fibonacci_backoff=True,  # 使用斐波那契退避模式 (3, 5, 8, 13, 21, ...)
            backoff_max=60,  # 最大等待时间 60 秒
        )

        if result.success:
            log.success(f"DomainMail 验证码获取成功: {result.data}")
            # 获取成功后，将邮件标记为已读
            if email_id_holder[0]:
                success, error = self.mark_email_as_read(email_id_holder[0])
                if success:
                    log.info("邮件已标记为已读", icon="check")
                else:
                    log.warning(f"标记已读失败: {error}")
            return result.data, None, email_time_holder[0]
        else:
            log.error(f"DomainMail 验证码获取失败 ({result.error})")
            return None, "未能获取验证码", None

    def get_verification_code_with_retry(
        self,
        address: str,
        max_retries: int = None,
        interval: int = None,
        retry_on_fail: bool = True,
        retry_wait: int = 10,
    ) -> tuple[str, str, str]:
        """获取验证码，支持验证码错误后的额外重试

        此方法供外部调用，当验证码输入失败时，可以等待后再次获取新验证码。

        Args:
            address: 邮箱地址
            max_retries: 最大重试次数
            interval: 轮询间隔 (秒)
            retry_on_fail: 是否在失败时重试
            retry_wait: 重试前等待时间 (秒)

        Returns:
            tuple: (code, error, email_time) - 验证码、错误信息、邮件时间
        """
        code, error, email_time = self.get_verification_code(
            address, max_retries, interval
        )

        if code:
            return code, error, email_time

        # 第一次获取失败，且启用了重试
        if retry_on_fail and not code:
            log.info(f"等待 {retry_wait} 秒后重新尝试获取验证码...", icon="wait")
            time.sleep(retry_wait)
            return self.get_verification_code(address, max_retries, interval)

        return code, error, email_time


domainmail_service = DomainMailService()


# ==================== 原有 KYX 邮箱服务 ====================


def generate_random_email() -> str:
    """生成随机邮箱地址: {random_str}oaiteam@{random_domain}"""
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    domain = get_random_domain()
    email = f"{random_str}oaiteam@{domain}"
    log.success(f"生成邮箱: {email}")
    return email


def create_email_user(
    email: str, password: str = None, role_name: str = None
) -> tuple[bool, str]:
    """在邮箱平台创建用户 (与 main.py 一致)

    Args:
        email: 邮箱地址
        password: 密码，默认使用 DEFAULT_PASSWORD
        role_name: 角色名，默认使用 EMAIL_ROLE

    Returns:
        tuple: (success, message)
    """
    if password is None:
        password = DEFAULT_PASSWORD
    if role_name is None:
        role_name = EMAIL_ROLE

    url = f"{EMAIL_API_BASE}/addUser"
    headers = {"Authorization": EMAIL_API_AUTH, "Content-Type": "application/json"}
    payload = {"list": [{"email": email, "password": password, "roleName": role_name}]}

    try:
        log.info(f"创建邮箱用户: {email}", icon="email")
        response = http_session.post(
            url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        success = data.get("code") == 200
        msg = data.get("message", "Unknown error")

        if success:
            log.success("邮箱创建成功")
        else:
            log.warning(f"邮箱创建失败: {msg}")

        return success, msg
    except Exception as e:
        log.error(f"邮箱创建异常: {e}")
        return False, str(e)


def get_verification_code(
    email: str, max_retries: int = None, interval: int = None
) -> tuple[str, str, str]:
    """从邮箱获取验证码 (使用通用轮询重试)

    Args:
        email: 邮箱地址
        max_retries: 最大重试次数
        interval: 基础轮询间隔 (秒)

    Returns:
        tuple: (code, error, email_time) - 验证码、错误信息、邮件时间
    """
    url = f"{EMAIL_API_BASE}/emailList"
    headers = {"Authorization": EMAIL_API_AUTH, "Content-Type": "application/json"}
    payload = {"toEmail": email}

    log.info(f"等待验证码邮件: {email}", icon="email")

    # 记录初始邮件数量，用于检测新邮件
    initial_email_count = 0
    try:
        response = http_session.post(
            url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        if data.get("code") == 200:
            initial_email_count = len(data.get("data", []))
    except Exception:
        pass

    # 用于存储邮件时间的闭包变量
    email_time_holder = [None]

    def fetch_emails():
        """获取邮件列表"""
        response = http_session.post(
            url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        data = response.json()
        if data.get("code") == 200:
            emails = data.get("data", [])
            # 只返回有新邮件时的数据
            if emails and len(emails) > initial_email_count:
                return emails
        return None

    def extract_code_from_subject(subject: str) -> str:
        """从主题中提取验证码 (优先匹配有上下文的验证码)"""
        if not subject:
            return None

        # 优先使用带上下文的正则模式 (避免匹配邮箱地址中的数字)
        patterns_with_context = [
            r"代码为\s*(\d{6})",
            r"code is\s*(\d{6})",
            r"verification code[:\s]*(\d{6})",
            r"验证码[：:\s]*(\d{6})",
            r"Your code is[:\s]*(\d{6})",
            r"one-time code[:\s]*(\d{6})",
            r"一次性验证码[：:\s]*(\d{6})",
        ]

        for pattern in patterns_with_context:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                return match.group(1)

        # 备用方案: 匹配独立的6位数字 (排除邮箱地址中的数字)
        subject_cleaned = re.sub(r'\S+@\S+', '', subject)
        match = re.search(r'\b(\d{6})\b', subject_cleaned)
        if match:
            return match.group(1)

        return None

    def check_for_code(emails):
        """检查邮件中是否有验证码"""
        latest_email = emails[0]
        subject = latest_email.get("subject", "")
        email_time_holder[0] = latest_email.get("createTime", "")

        code = extract_code_from_subject(subject)
        return code

    # 使用通用轮询函数
    result = poll_with_retry(
        fetch_func=fetch_emails,
        check_func=check_for_code,
        max_retries=max_retries,
        interval=interval,
        description="获取邮件",
    )

    if result.success:
        log.success(f"验证码获取成功: {result.data}")
        return result.data, None, email_time_holder[0]
    else:
        log.error(f"验证码获取失败 ({result.error})")
        return None, "未能获取验证码", None


def fetch_email_content(email: str) -> list:
    """获取邮箱中的邮件列表

    Args:
        email: 邮箱地址

    Returns:
        list: 邮件列表
    """
    url = f"{EMAIL_API_BASE}/emailList"
    headers = {"Authorization": EMAIL_API_AUTH, "Content-Type": "application/json"}
    payload = {"toEmail": email}

    try:
        response = http_session.post(
            url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        data = response.json()

        if data.get("code") == 200:
            return data.get("data", [])
    except Exception as e:
        log.warning(f"获取邮件列表异常: {e}")

    return []


def batch_create_emails(count: int = 4) -> list:
    """批量创建邮箱 (根据 EMAIL_PROVIDER 配置自动选择邮箱系统)

    Args:
        count: 创建数量

    Returns:
        list: [{"email": "...", "password": "..."}, ...]
    """
    accounts = []

    for i in range(count):
        email, password = unified_create_email()

        if email:
            accounts.append({"email": email, "password": password})
        else:
            log.warning(f"跳过第 {i + 1} 个邮箱创建")

    log.info(f"邮箱创建完成: {len(accounts)}/{count}", icon="email")
    return accounts


# ==================== 统一邮箱接口 (根据配置自动选择) ====================


def unified_generate_email() -> str:
    """统一生成邮箱地址接口 (根据 EMAIL_PROVIDER 配置自动选择)

    Returns:
        str: 邮箱地址
    """
    if EMAIL_PROVIDER == "domainmail":
        random_str = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        domain = get_random_domainmail_domain()
        if domain:
            email = f"{random_str}oaiteam@{domain}"
            return email
        log.warning("DomainMail 无可用域名，回退到 KYX")

    if EMAIL_PROVIDER == "gptmail":
        random_str = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        prefix = f"{random_str}-oaiteam"
        domain = get_random_gptmail_domain() or None
        email, error = gptmail_service.generate_email(prefix=prefix, domain=domain)
        if email:
            return email
        log.warning(f"GPTMail 生成失败，回退到 KYX: {error}")

    return generate_random_email()


def unified_create_email() -> tuple[str, str]:
    """统一创建邮箱接口 (根据 EMAIL_PROVIDER 配置自动选择)

    Returns:
        tuple: (email, password)
    """
    if EMAIL_PROVIDER == "domainmail":
        from datetime import datetime

        now = datetime.now()
        mm = now.strftime("%m")
        dd = now.strftime("%d")
        random_str = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )
        prefix = f"gpt-{mm}{dd}{random_str}"

        domain = get_random_domainmail_domain()
        if domain:
            email = f"{prefix}@{domain}"
            mailbox, error = domainmail_service.create_mailbox(email)
            if mailbox:
                return email, DEFAULT_PASSWORD
            log.warning(f"DomainMail 创建失败: {error}")
        else:
            log.warning("DomainMail 无可用域名，回退到 KYX")

    if EMAIL_PROVIDER == "gptmail":
        random_str = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=8)
        )
        prefix = f"{random_str}-oaiteam"
        domain = get_random_gptmail_domain() or None
        email, error = gptmail_service.generate_email(prefix=prefix, domain=domain)
        if email:
            return email, DEFAULT_PASSWORD
        log.warning(f"GPTMail 生成失败，回退到 KYX: {error}")

    email = generate_random_email()
    success, msg = create_email_user(email, DEFAULT_PASSWORD)
    if success or "已存在" in msg:
        return email, DEFAULT_PASSWORD
    return None, None


def unified_get_verification_code(
    email: str, max_retries: int = None, interval: int = None
) -> tuple[str, str, str]:
    """统一获取验证码接口 (根据 EMAIL_PROVIDER 配置自动选择)

    Args:
        email: 邮箱地址
        max_retries: 最大重试次数
        interval: 轮询间隔 (秒)

    Returns:
        tuple: (code, error, email_time) - 验证码、错误信息、邮件时间
    """
    if EMAIL_PROVIDER == "domainmail":
        return domainmail_service.get_verification_code(email, max_retries, interval)

    if EMAIL_PROVIDER == "gptmail":
        return gptmail_service.get_verification_code(email, max_retries, interval)

    return get_verification_code(email, max_retries, interval)


def unified_fetch_emails(email: str) -> list:
    """统一获取邮件列表接口 (根据 EMAIL_PROVIDER 配置自动选择)

    Args:
        email: 邮箱地址

    Returns:
        list: 邮件列表
    """
    if EMAIL_PROVIDER == "gptmail":
        emails, error = gptmail_service.get_emails(email)
        return emails

    # 默认使用 KYX 系统
    return fetch_email_content(email)
