# -*- coding: utf-8 -*-
"""
Unsloth 训练器 - 快速 QLoRA 微调
支持 Qwen3-30B-A3B MoE，低显存，2倍速
"""
import os
import json
from typing import Dict, List

class UnslothTrainer:
    """Unsloth 训练器 - 实际训练逻辑"""
    
    def __init__(self):
        self.supported_models = ["qwen3-30b-a3b", "qwen2-7b", "llama3-8b"]
        self.is_available = self._check_unsloth()

    def _check_unsloth(self) -> bool:
        try:
            import unsloth
            return True
        except Exception:
            return False

    def generate_training_script(self, sft_file: str, output_dir: str, config: Dict) -> str:
        """生成训练脚本 - 用于 Windows 上执行"""
        
        script = f'''
# -*- coding: utf-8 -*-
"""
自动生成的微调脚本 - Qwen3-30B-A3B 自我进化
生成时间：{config.get("timestamp", "")}
训练样本：{config.get("samples", 0)}
"""

import os
os.environ["UNSLOTH_RETURN_LOGITS"] = "1"

# 检查 unsloth
try:
    from unsloth import FastLanguageModel
    import torch
    print("✅ Unsloth 可用")
except ImportError:
    print("❌ 请安装: pip install unsloth")
    exit(1)

# 配置
model_path = r"{config.get('model_path', 'D:\\llama.cpp\\Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ4_XS.gguf')}"
# 注意：gguf 需先转 hf 格式，或直接用 hf 模型
# 这里演示用 HF 模型路径
hf_model = "Qwen/Qwen3-30B-A3B"

print(f"加载模型: {{hf_model}}")
print(f"量化: 4bit, LoRA rank: {config.get('lora_rank', 32)}")

# 加载模型
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = hf_model,
    max_seq_length = 4096,
    dtype = None,
    load_in_4bit = True,
)

# LoRA 配置 - 针对 MoE 优化
model = FastLanguageModel.get_peft_model(
    model,
    r = {config.get('lora_rank', 32)},
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = {config.get('lora_alpha', 64)},
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
    use_rslora = False,
    loftq_config = None,
)

# 加载数据
from datasets import load_dataset
dataset = load_dataset("json", data_files="{sft_file}", split="train")

# 格式化
def formatting_prompts_func(examples):
    convos = examples["conversations"]
    texts = []
    for convo in convos:
        # ShareGPT 格式转 ChatML
        text = tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False)
        texts.append(text)
    return {{ "text" : texts }}

dataset = dataset.map(formatting_prompts_func, batched=True)

# 训练
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = 4096,
    dataset_num_proc = 2,
    packing = False,
    args = TrainingArguments(
        per_device_train_batch_size = 1,
        gradient_accumulation_steps = 8,
        warmup_steps = 5,
        num_train_epochs = 1,
        learning_rate = {config.get('learning_rate', 2e-4)},
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "{output_dir}",
    ),
)

print("开始训练...")
trainer_stats = trainer.train()

# 保存 LoRA
model.save_pretrained("{output_dir}")
tokenizer.save_pretrained("{output_dir}")
print(f"✅ LoRA 已保存到 {output_dir}")

# 合并测试（可选）
# model.save_pretrained_merged("{output_dir}_merged", tokenizer, save_method="merged_16bit")
'''
        return script

    def get_install_guide(self) -> Dict:
        """安装指南 - Windows"""
        return {
            "windows": {
                "steps": [
                    "pip install unsloth",
                    "pip install torch --index-url https://download.pytorch.org/whl/cu121",
                    "pip install trl transformers datasets accelerate",
                    "下载模型：huggingface-cli download Qwen/Qwen3-30B-A3B --local-dir D:\\models\\Qwen3-30B-A3B"
                ],
                "vram_required": "QLoRA 4bit 训练 Qwen3-30B-A3B 需要 ~24GB VRAM，推理需要 16GB",
                "cpu_fallback": "若显存不足，可用 CPU 训练，但慢 10 倍",
                "note": "你的 IQ4_XS gguf 需先转 HF 格式，或直接用 HF 模型训练"
            },
            "training_time": {
                "100_samples": "约 15 分钟 (RTX 4090)",
                "300_samples": "约 40 分钟",
                "1000_samples": "约 2 小时"
            }
        }

unsloth_trainer = UnslothTrainer()
