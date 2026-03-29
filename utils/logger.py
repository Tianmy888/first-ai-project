# utils/logger.py
import logging
import json
from datetime import datetime
from pathlib import Path

# 创建日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name: str, log_file: str, level=logging.INFO):
    """配置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    file_handler = logging.FileHandler(LOG_DIR / log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建日志记录器
request_logger = setup_logger("request_logger", "requests.log")
error_logger = setup_logger("error_logger", "errors.log")
cost_logger = setup_logger("cost_logger", "cost.log")

def log_translation_call(text: str, target_lang: str, tokens_used: int, 
                         duration_ms: int, success: bool, error: str = None):
    """记录翻译请求"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "translation",
        "text_length": len(text),
        "target_lang": target_lang,
        "tokens_used": tokens_used,
        "duration_ms": duration_ms,
        "success": success
    }
    
    if error:
        log_entry["error"] = error
        error_logger.error(json.dumps(log_entry))
    else:
        request_logger.info(json.dumps(log_entry))
    
    # 成本记录（GPT-3.5约$0.002/1K tokens）
    estimated_cost = tokens_used * 0.000002
    cost_logger.info(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "type": "translation",
        "tokens_used": tokens_used,
        "estimated_cost_usd": round(estimated_cost, 6)
    }))

def log_chat_call(session_id: str, message: str, tokens_used: int,
                  duration_ms: int, success: bool, error: str = None):
    """记录对话请求"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "chat",
        "session_id": session_id,
        "message_length": len(message),
        "tokens_used": tokens_used,
        "duration_ms": duration_ms,
        "success": success
    }
    
    if error:
        log_entry["error"] = error
        error_logger.error(json.dumps(log_entry))
    else:
        request_logger.info(json.dumps(log_entry))

def get_cost_stats():
    """获取成本统计"""
    cost_file = LOG_DIR / "cost.log"
    if not cost_file.exists():
        return {"total_cost": 0, "total_tokens": 0, "requests": 0}
    
    total_tokens = 0
    total_cost = 0
    requests = 0
    
    with open(cost_file, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                total_tokens += data.get("tokens_used", 0)
                total_cost += data.get("estimated_cost_usd", 0)
                requests += 1
            except:
                pass
    
    return {
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "requests": requests
    }