# 在翻译函数中添加日志
from utils.logger import log_translation_call
import time

# 在翻译函数开始记录时间
start_time = time.time()

# 在返回结果前记录日志
duration_ms = int((time.time() - start_time) * 1000)
log_translation_call(
    text=text,
    target_lang=target_lang,
    tokens_used=response.usage.total_tokens,
    duration_ms=duration_ms,
    success=True
)