# -*- coding: utf-8 -*-
"""
阈值验证脚本 v0914 - 验证不同阈值对回放效果的影响
- 0.8阈值无理论依据，改为可配置，提供验证脚本让作者跑几组数据看影响再定默认值
"""
import os
import sys
import json
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_threshold_impact():
    """测试不同阈值对回放效果的影响"""
    print("=== 阈值验证脚本 v0914 ===")
    print("目的：验证不同min_quality阈值对Replay Buffer的影响，确定合理默认值")
    print("背景：0.8阈值无理论依据，需实验确定\n")
    
    # 模拟数据 - 如果真实数据不存在
    base_dir = Path(__file__).parent.parent
    sft_path = base_dir / "data" / "training" / "sft.jsonl"
    
    all_samples = []
    
    if sft_path.exists():
        try:
            with open(sft_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        all_samples.append(data)
                    except:
                        continue
            print(f"✅ 读取真实训练数据：{len(all_samples)}条 来自 {sft_path}")
        except Exception as e:
            print(f"⚠️ 读取真实数据失败: {e}，使用模拟数据")
    
    if not all_samples:
        # 生成模拟数据
        print("📝 生成模拟训练数据用于阈值验证")
        # 模拟不同质量分数分布
        for i in range(200):
            # 正态分布模拟质量分数，集中在0.6-0.8
            quality = random.gauss(0.65, 0.2)
            quality = max(0.1, min(0.95, quality))
            
            all_samples.append({
                "id": f"sample_{i}",
                "importance_score": quality,
                "quality_score": quality + random.uniform(-0.1, 0.1),
                "conversations": [
                    {"from": "human", "value": f"任务 {i}"},
                    {"from": "gpt", "value": f"执行任务 {i}"}
                ],
                "task_type": random.choice(["file", "system", "window", "security", "network"]),
                "source": "simulated"
            })
        print(f"   生成模拟数据：{len(all_samples)}条，质量分数正态分布 μ=0.65 σ=0.2")
    
    total = len(all_samples)
    print(f"\n总样本数：{total}")
    
    # 统计质量分数分布
    qualities = [s.get("importance_score", 0.5) for s in all_samples]
    qualities.sort()
    
    print(f"\n质量分数分布：")
    print(f"  最低: {min(qualities):.3f}")
    print(f"  最高: {max(qualities):.3f}")
    print(f"  平均: {sum(qualities)/len(qualities):.3f}")
    print(f"  中位数: {qualities[len(qualities)//2]:.3f}")
    print(f"  0.5分位数: {qualities[int(len(qualities)*0.5)]:.3f}")
    print(f"  0.8分位数: {qualities[int(len(qualities)*0.8)]:.3f}")
    
    # 测试不同阈值
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    ratio = 0.3  # Replay比例
    
    print(f"\n{'阈值':<8} {'高质量数':<12} {'高质量比例':<15} {'Replay数':<12} {'Replay/总数':<15} {'建议'}")
    print("-"*80)
    
    results = {}
    
    for thresh in thresholds:
        high_quality = [
            s for s in all_samples 
            if s.get("importance_score", 0.5) >= thresh or s.get("quality_score", 0.5) >= thresh
        ]
        high_count = len(high_quality)
        high_ratio = high_count / total if total > 0 else 0
        replay_count = max(1, int(high_count * ratio)) if high_count > 0 else 0
        replay_ratio = replay_count / total if total > 0 else 0
        
        # 评估建议
        if high_ratio < 0.1:
            suggestion = "⚠️ 过少，多样性不足"
        elif high_ratio > 0.6:
            suggestion = "⚠️ 过多，质量筛选弱"
        elif 0.2 <= high_ratio <= 0.4:
            suggestion = "✅ 合理，平衡质量数量"
        else:
            suggestion = "◐ 可接受"
        
        if thresh == 0.8:
            suggestion += " (当前默认)"
        
        print(f"{thresh:<8} {high_count:<12} {high_ratio:<15.3f} {replay_count:<12} {replay_ratio:<15.3f} {suggestion}")
        
        results[thresh] = {
            "threshold": thresh,
            "high_quality_count": high_count,
            "high_quality_ratio": high_ratio,
            "replay_count": replay_count,
            "replay_ratio": replay_ratio,
            "total": total
        }
    
    print("\n" + "="*60)
    print("分析与建议：")
    print("="*60)
    
    # 找出合理阈值
    reasonable = [(t, r) for t, r in results.items() if 0.15 <= r["high_quality_ratio"] <= 0.5]
    
    if reasonable:
        print(f"✅ 合理阈值区间（高质量比例15%-50%）：")
        for thresh, data in reasonable:
            print(f"   - 阈值 {thresh}: 高质量 {data['high_quality_ratio']:.1%} -> Replay {data['replay_count']}条")
        
        # 推荐
        best = min(reasonable, key=lambda x: abs(x[1]["high_quality_ratio"] - 0.3))  # 接近30%最佳
        print(f"\n💡 推荐阈值：{best[0]} (高质量比例最接近30%，平衡质量与数量)")
    else:
        print("⚠️ 无合理阈值，建议检查数据质量分布或调整ratio")
    
    print(f"\n当前默认阈值0.8：")
    current = results.get(0.8)
    if current:
        if current["high_quality_ratio"] < 0.1:
            print(f"  ⚠️ 阈值0.8过高，仅 {current['high_quality_ratio']:.1%} 样本通过，可能导致Replay多样性不足")
            print(f"  建议：降低到0.6-0.7，增加高质量样本数量")
        elif current["high_quality_ratio"] > 0.5:
            print(f"  ⚠️ 阈值0.8过低，{current['high_quality_ratio']:.1%} 样本通过，质量筛选作用弱")
            print(f"  建议：提高到0.85-0.9，更严格筛选")
        else:
            print(f"  ✅ 阈值0.8合理，{current['high_quality_ratio']:.1%} 通过")
    
    # 保存结果
    result_path = Path(__file__).parent / "threshold_validation_result.json"
    try:
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump({
                "total_samples": total,
                "quality_stats": {
                    "min": min(qualities),
                    "max": max(qualities),
                    "mean": sum(qualities)/len(qualities),
                    "median": qualities[len(qualities)//2]
                },
                "thresholds": results,
                "reasonable_thresholds": [t for t, _ in reasonable],
                "recommended": best[0] if reasonable else None,
                "note": "0.8阈值无理论依据，需实验确定，此脚本提供数据支持"
            }, f, ensure_ascii=False, indent=2)
        print(f"\n📄 结果已保存：{result_path}")
    except Exception as e:
        print(f"保存结果失败: {e}")
    
    print("\n" + "="*60)
    print("下一步：")
    print("1. 根据此脚本结果，调整config/replay_config.json中的min_quality")
    print("2. 跑真实训练，对比不同阈值下的模型效果")
    print("3. 选择在验证集上效果最好的阈值作为默认值")
    print("4. 环境变量ZANE_REPLAY_QUALITY可临时覆盖测试")
    
    return results


def test_replay_config():
    """测试Replay配置可配置性"""
    print("\n=== 测试Replay配置可配置性 ===")
    
    try:
        from backend.learning.replay_buffer import replay_buffer
        
        config = replay_buffer.config
        print(f"当前配置：{config}")
        print(f"配置文件：{replay_buffer.config_path}")
        
        # 测试不同阈值构建
        for thresh in [0.6, 0.8]:
            result = replay_buffer.build(min_quality=thresh)
            print(f"阈值{thresh}构建结果：Replay {result.get('replay_count',0)}条，总高质量{result.get('total_high_quality',0)}条")
        
        # 验证方法
        validation = replay_buffer.validate_thresholds()
        print(f"\n验证方法结果：{validation.get('total_samples',0)}总样本")
        for thresh, data in validation.get('thresholds', {}).items():
            print(f"  阈值{thresh}: 高质量{data['high_quality_ratio']:.1%} Replay{data['replay_count']}条")
        
        print("✅ Replay配置可配置性测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Zane v0914 阈值验证脚本")
    print("="*60)
    
    results = test_threshold_impact()
    print("\n")
    test_replay_config()
    
    print("\n" + "="*60)
    print("✅ 阈值验证完成 - 0.8阈值已改为可配置，支持实验确定合理值")
