from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict, Counter
import statistics


class SummaryGenerator:
    """Generates summary reports from analysis results."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def _log(self, message: str):
        if self.verbose:
            print(f"[SummaryGenerator] {message}")
    
    def generate_summary(self, repository_path: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._log("Generating summary statistics...")
        if not results:
            return self._empty_summary(repository_path)
        
        summary = {
            'repository': {
                'location': repository_path,
                'analyzed_at': datetime.now().isoformat(),
                'commit_count': len(results)
            }
        }
        
        java_stats = self._calculate_java_statistics(results)
        summary['java_files'] = java_stats
        
        warning_stats = self._calculate_warning_statistics(results)
        summary['warnings'] = warning_stats
        
        temporal_stats = self._calculate_temporal_trends(results)
        summary['temporal_trends'] = temporal_stats
        
        rule_stats = self._calculate_rule_statistics(results)
        summary['rule_statistics'] = rule_stats
        
        quality_metrics = self._calculate_quality_metrics(results)
        summary['quality_metrics'] = quality_metrics
        
        # 生成符合要求的格式
        summary['formatted_summary'] = self._generate_formatted_summary(summary)
        
        return summary
    
    def _empty_summary(self, repository_path: str) -> Dict[str, Any]:
        return {
            'repository': {
                'location': repository_path,
                'analyzed_at': datetime.now().isoformat(),
                'commit_count': 0
            },
            'java_files': {'average_count': 0},
            'warnings': {'average_count': 0},
            'warning_statistics': {},
            'formatted_summary': {
                "location": repository_path,
                "stat_of_repository": {
                    "number_of_commits": 0,
                    "avg_of_num_java_files": 0,
                    "avg_of_num_warnings": 0
                },
                "stat_of_warnings": {}
            }
        }
    
    def _calculate_java_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        java_counts = [r['java_files']['count'] for r in results]
        total_lines = [r['java_files']['total_lines'] for r in results]
        return {
            'average_count': statistics.mean(java_counts) if java_counts else 0,
            'median_count': statistics.median(java_counts) if java_counts else 0,
            'min_count': min(java_counts) if java_counts else 0,
            'max_count': max(java_counts) if java_counts else 0,
            'total_commits': len(java_counts),
            'average_total_lines': statistics.mean(total_lines) if total_lines else 0,
            'median_total_lines': statistics.median(total_lines) if total_lines else 0
        }
    
    def _calculate_warning_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        warning_counts = [r['pmd_analysis']['violation_count'] for r in results]
        files_with_violations = [r['pmd_analysis']['files_with_violations'] for r in results]
        all_violations = []
        for result in results:
            all_violations.extend(result['pmd_analysis']['violations'])
        priority_counts = Counter()
        for violation in all_violations:
            priority_counts[violation.get('priority', 0)] += 1
        return {
            'average_count': statistics.mean(warning_counts) if warning_counts else 0,
            'median_count': statistics.median(warning_counts) if warning_counts else 0,
            'min_count': min(warning_counts) if warning_counts else 0,
            'max_count': max(warning_counts) if warning_counts else 0,
            'total_violations': sum(warning_counts),
            'average_files_with_violations': statistics.mean(files_with_violations) if files_with_violations else 0,
            'priority_distribution': dict(priority_counts)
        }
    
    def _calculate_temporal_trends(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        sorted_results = sorted(results, key=lambda x: x['commit']['timestamp'])
        timestamps = [r['commit']['timestamp'] for r in sorted_results]
        java_counts = [r['java_files']['count'] for r in sorted_results]
        warning_counts = [r['pmd_analysis']['violation_count'] for r in sorted_results]

        def calculate_trend(values):
            if len(values) < 2:
                return 0
            n = len(values)
            x_mean = (n - 1) / 2
            y_mean = statistics.mean(values)
            numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            return numerator / denominator if denominator != 0 else 0

        return {
            'java_files_trend': calculate_trend(java_counts),
            'warnings_trend': calculate_trend(warning_counts),
            'first_commit_date': datetime.fromtimestamp(timestamps[0]).isoformat() if timestamps else None,
            'last_commit_date': datetime.fromtimestamp(timestamps[-1]).isoformat() if timestamps else None,
            'analysis_period_days': (timestamps[-1] - timestamps[0]) / 86400 if len(timestamps) > 1 else 0
        }
    
    def _calculate_rule_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        rule_violations = defaultdict(int)
        rule_commits = defaultdict(set)
        for result in results:
            commit_hash = result['commit']['hash']
            for violation in result['pmd_analysis']['violations']:
                rule = violation.get('rule', 'Unknown')
                rule_violations[rule] += 1
                rule_commits[rule].add(commit_hash)
        rule_stats = {}
        for rule, count in rule_violations.items():
            rule_stats[rule] = {
                'total_violations': count,
                'commits_affected': len(rule_commits[rule]),
                'average_per_commit': count / len(results) if results else 0
            }
        return rule_stats
    
    def _calculate_quality_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not results:
            return {}
        violation_densities = []
        for result in results:
            total_lines = result['java_files']['total_lines']
            violations = result['pmd_analysis']['violation_count']
            if total_lines > 0:
                density = (violations / total_lines) * 1000
                violation_densities.append(density)
        file_quality_ratios = []
        for result in results:
            java_count = result['java_files']['count']
            files_with_violations = result['pmd_analysis']['files_with_violations']
            if java_count > 0:
                clean_ratio = (java_count - files_with_violations) / java_count
                file_quality_ratios.append(clean_ratio)
        return {
            'average_violation_density': statistics.mean(violation_densities) if violation_densities else 0,
            'median_violation_density': statistics.median(violation_densities) if violation_densities else 0,
            'average_clean_file_ratio': statistics.mean(file_quality_ratios) if file_quality_ratios else 0,
            'median_clean_file_ratio': statistics.median(file_quality_ratios) if file_quality_ratios else 0
        }
    
    def _generate_formatted_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Reformat summary to required nested structure with renamed keys."""
        return {
            "location": summary["repository"]["location"],
            "stat_of_repository": {
                "number_of_commits": summary["repository"]["commit_count"],
                "avg_of_num_java_files": summary["java_files"]["average_count"],
                "avg_of_num_warnings": summary["warnings"]["average_count"]
            },
            "stat_of_warnings": {
                k: v for k, v in summary["warnings"].items()
                if k != "average_count"
            }
        }
