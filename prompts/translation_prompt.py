# prompts/translation_prompt.py

# ========== Prompt版本演进记录 ==========
# 面试时可以讲述每个版本的优化原因

PROMPT_VERSIONS = {
    "v1.0": """
        将以下文本翻译成 {target_lang} 语言：
        {text}
    """,
    
    "v1.1": """
        你是一个专业的翻译助手。请将以下文本翻译成 {target_lang} 语言。
        
        要求：
        1. 保持原文的语气和风格
        2. 专业术语准确翻译
        
        原文：{text}
        译文：
    """,
    
    "v2.0": """
        你是一个专业的翻译助手。请将以下文本翻译成 {target_lang} 语言。
        
        翻译原则：
        1. 准确性：专业术语必须准确（如：深度学习 → deep learning）
        2. 流畅性：符合目标语言表达习惯
        3. 文化适配：俚语、习语进行意译（如：吃土 → spend all one's money）
        4. 一致性：专有名词保持统一
        
        原文：{text}
        译文：
    """,
    
    "v2.1": """
        你是一个专业的翻译助手。请将以下文本翻译成 {target_lang} 语言。
        
        翻译原则：
        1. 准确性：专业术语必须准确
        2. 流畅性：符合目标语言表达习惯
        3. 文化适配：俚语、习语进行意译
        4. 一致性：专有名词保持统一
        
        Few-shot 示例：
        输入：深度学习在图像识别领域取得了突破
        输出：Deep learning has made breakthroughs in the field of image recognition
        
        输入：这个月又要吃土了
        输出：I'm going to have to tighten my belt this month
        
        输入：锦鲤附体，这次考试过了
        输出：Lucky charm worked, I passed the exam
        
        原文：{text}
        译文：
    """,
    
    "v3.0": """
        你是一个专业的翻译助手。请将以下文本翻译成 {target_lang} 语言。
        
        翻译原则：
        1. 准确性：专业术语必须准确
        2. 流畅性：符合目标语言表达习惯
        3. 文化适配：俚语、习语进行意译
        4. 一致性：专有名词保持统一
        5. 长句处理：对复杂长句进行合理断句，保持语序通顺
        
        Few-shot 示例：
        输入：深度学习在图像识别领域取得了突破
        输出：Deep learning has made breakthroughs in the field of image recognition
        
        输入：尽管面临诸多挑战，但团队依然坚持不懈，最终成功完成了项目
        输出：Despite facing numerous challenges, the team persevered and ultimately succeeded in completing the project
        
        原文：{text}
        译文：
    """
}

# 当前使用的版本
CURRENT_PROMPT_VERSION = "v3.0"

# ========== Badcase 迭代记录 ==========
# 展示问题发现、分析根因、优化方案的产品思维

BAD_CASE_ITERATIONS = [
    {
        "version": "v1.0",
        "badcase": "深度学习 → deep study",
        "根因": "模型缺乏专业术语知识",
        "优化方案": "v1.1 增加'专业术语准确翻译'要求"
    },
    {
        "version": "v1.1",
        "badcase": "吃土 → eat dirt",
        "根因": "模型不理解俚语，直译",
        "优化方案": "v2.0 增加'文化适配'原则，要求意译"
    },
    {
        "version": "v2.0",
        "badcase": "锦鲤 → koi fish (直译，未体现文化含义)",
        "根因": "模型对网络流行语理解不足",
        "优化方案": "v2.1 增加 Few-shot 示例，让模型学习正确译法"
    },
    {
        "version": "v2.1",
        "badcase": "复杂长句翻译后语序混乱",
        "根因": "模型对长句处理能力不足",
        "优化方案": "v3.0 增加长句处理原则，优化断句逻辑"
    }
]

def get_translation_prompt(target_lang: str, text: str) -> str:
    """获取当前版本的翻译Prompt"""
    lang_names = {
        "zh": "中文", "en": "英文", "ja": "日文",
        "ko": "韩文", "fr": "法文", "de": "德文", "es": "西班牙文"
    }
    target_lang_name = lang_names.get(target_lang, target_lang)
    prompt_template = PROMPT_VERSIONS[CURRENT_PROMPT_VERSION]
    return prompt_template.format(target_lang=target_lang_name, text=text)

def get_prompt_version_info():
    """获取Prompt版本信息（用于API展示）"""
    return {
        "current_version": CURRENT_PROMPT_VERSION,
        "versions": list(PROMPT_VERSIONS.keys()),
        "badcase_iterations": BAD_CASE_ITERATIONS
    }