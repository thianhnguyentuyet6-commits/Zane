# -*- coding: utf-8 -*-
"""
技能基因进化 - 基因交叉变异优胜劣汰
- 技能基因 code+tests+success+fitness
- 适应度 success/(success+failure)*importance
- 变异交叉选择复合改进
"""
import os
import json
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class SkillGene:
    id: str
    name: str
    description: str
    code: str
    tests: List[Dict]
    success_count: int
    failure_count: int
    importance: float
    fitness: float
    parent: List[str]
    created_at: float
    last_used: float
    generation: int

class SkillGeneEvolution:
    """技能基因进化"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.join(os.path.dirname(__file__), "..", "..")).resolve()
        self.genes_dir = self.base_dir / "data" / "skill_genes"
        self.genes_dir.mkdir(parents=True, exist_ok=True)
        self.genes: List[SkillGene] = []
        self.load()
    
    def load(self):
        # 从skill_library加载
        try:
            from .skill_library import skill_library
            for skill in skill_library.skills:
                gene = SkillGene(
                    id=skill.name,
                    name=skill.name,
                    description=skill.description,
                    code=skill.code,
                    tests=skill.tests,
                    success_count=skill.success_count,
                    failure_count=skill.failure_count,
                    importance=0.7,
                    fitness=self.calc_fitness(skill.success_count, skill.failure_count, 0.7),
                    parent=[],
                    created_at=skill.created_at,
                    last_used=skill.last_used,
                    generation=1
                )
                self.genes.append(gene)
        except Exception:
            pass
        
        # 从文件加载
        for path in self.genes_dir.glob("*.json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    gene = SkillGene(**data)
                    if not any(g.id == gene.id for g in self.genes):
                        self.genes.append(gene)
            except Exception:
                continue
    
    def save(self, gene: SkillGene):
        path = self.genes_dir / f"{gene.id}.json"
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(asdict(gene), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存基因失败: {e}")
    
    def calc_fitness(self, success: int, failure: int, importance: float) -> float:
        """适应度 success/(success+failure)*importance"""
        total = success + failure
        if total == 0:
            return importance * 0.5
        rate = success / total
        return round(rate * importance, 3)
    
    def mutate(self, gene: SkillGene) -> SkillGene:
        """变异：随机改参数"""
        mutations = [
            ("整理下载", "整理文档"),
            ("Downloads", "Documents"),
            ("list_files", "search_files"),
            ("create_folder", "create_folder"),
        ]
        
        new_code = gene.code
        new_desc = gene.description
        
        # 随机变异
        old, new = random.choice(mutations)
        new_code = new_code.replace(old, new)
        new_desc = new_desc.replace(old, new)
        
        new_gene = SkillGene(
            id=f"{gene.id}_mut_{int(time.time()*1000)%10000}",
            name=f"{gene.name}_变异",
            description=new_desc + " (变异)",
            code=new_code,
            tests=gene.tests,
            success_count=0,
            failure_count=0,
            importance=gene.importance,
            fitness=0,
            parent=[gene.id],
            created_at=time.time(),
            last_used=time.time(),
            generation=gene.generation + 1
        )
        
        return new_gene
    
    def crossover(self, gene1: SkillGene, gene2: SkillGene) -> SkillGene:
        """交叉：两个技能组合"""
        # 组合code
        combined_code = f"""
# 组合技能：{gene1.name} + {gene2.name}
# 来自 {gene1.id} 和 {gene2.id}

def combined_{gene1.id}_{gene2.id}(path: str):
    \"\"\"组合：{gene1.description} + {gene2.description}\"\"\"
    # 步骤1：{gene1.name}
    {gene1.code[:100]}
    # 步骤2：{gene2.name}
    {gene2.code[:100]}
    return {{"success": True, "combined": True}}
"""
        
        new_gene = SkillGene(
            id=f"cross_{gene1.id}_{gene2.id}_{int(time.time())%10000}",
            name=f"{gene1.name}+{gene2.name}",
            description=f"组合技能：{gene1.description} + {gene2.description}",
            code=combined_code,
            tests=gene1.tests + gene2.tests[:1],
            success_count=0,
            failure_count=0,
            importance=(gene1.importance + gene2.importance) / 2,
            fitness=0,
            parent=[gene1.id, gene2.id],
            created_at=time.time(),
            last_used=time.time(),
            generation=max(gene1.generation, gene2.generation) + 1
        )
        
        return new_gene
    
    def select(self, threshold_high: float = 0.7, threshold_low: float = 0.3) -> Dict[str, Any]:
        """选择：>0.7保留 <0.3遗忘"""
        retained = []
        forgotten = []
        
        for gene in self.genes:
            # 更新fitness
            gene.fitness = self.calc_fitness(gene.success_count, gene.failure_count, gene.importance)
            
            if gene.fitness >= threshold_high:
                retained.append(gene)
            elif gene.fitness < threshold_low and gene.success_count + gene.failure_count > 3:
                forgotten.append(gene)
        
        # 删除遗忘的
        for gene in forgotten:
            try:
                path = self.genes_dir / f"{gene.id}.json"
                if path.exists():
                    path.unlink()
                self.genes.remove(gene)
            except Exception:
                pass
        
        return {
            "total": len(self.genes) + len(forgotten),
            "retained": len(retained),
            "forgotten": len(forgotten),
            "retained_ids": [g.id for g in retained],
            "forgotten_ids": [g.id for g in forgotten],
            "fitness_distribution": {
                "high": len([g for g in self.genes if g.fitness >= 0.7]),
                "medium": len([g for g in self.genes if 0.3 <= g.fitness < 0.7]),
                "low": len([g for g in self.genes if g.fitness < 0.3])
            }
        }
    
    def evolve(self, num_mutations: int = 2, num_crossovers: int = 2) -> Dict[str, Any]:
        """进化一轮"""
        # 按fitness排序
        sorted_genes = sorted(self.genes, key=lambda x: x.fitness, reverse=True)
        top_genes = sorted_genes[:5] if len(sorted_genes) >= 5 else sorted_genes
        
        new_genes = []
        
        # 变异
        for i in range(num_mutations):
            if top_genes:
                parent = random.choice(top_genes)
                mutated = self.mutate(parent)
                self.genes.append(mutated)
                self.save(mutated)
                new_genes.append(mutated)
        
        # 交叉
        for i in range(num_crossovers):
            if len(top_genes) >= 2:
                g1, g2 = random.sample(top_genes, 2)
                crossed = self.crossover(g1, g2)
                self.genes.append(crossed)
                self.save(crossed)
                new_genes.append(crossed)
        
        # 选择
        selection = self.select()
        
        # 复合改进：技能调用技能
        composite = []
        if len(self.genes) >= 2:
            for gene in self.genes[:3]:
                if "organize" in gene.name or "整理" in gene.description:
                    # 组织类技能可调用其他
                    composite.append(f"{gene.name} 可调用 {random.choice(self.genes).name}")
        
        return {
            "total": len(self.genes),
            "new": len(new_genes),
            "new_genes": [asdict(g) for g in new_genes],
            "selection": selection,
            "composite": composite,
            "best": asdict(sorted_genes[0]) if sorted_genes else None,
            "note": "技能基因进化 变异交叉选择复合改进"
        }
    
    def get_evolution_tree(self) -> Dict[str, Any]:
        """获取进化树"""
        tree = {}
        for gene in self.genes:
            tree[gene.id] = {
                "name": gene.name,
                "fitness": gene.fitness,
                "generation": gene.generation,
                "parent": gene.parent,
                "success": gene.success_count,
                "failure": gene.failure_count
            }
        
        return {
            "total": len(self.genes),
            "tree": tree,
            "generations": max([g.generation for g in self.genes], default=0),
            "best_fitness": max([g.fitness for g in self.genes], default=0)
        }

# 全局
skill_gene_evolution = SkillGeneEvolution()
