"""
Summary Generator
Generates summary statistics and reports from all commit analysis results.
"""

from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict, Counter
import statistics


class SummaryGenerator:
    """Generates summary reports from analysis results."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize SummaryGenerator.
        
        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
    
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[SummaryGenerator] {message}")
    
    def generate_summary(self, repository_path: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive summary from all commit results.
        
        Args:
            repository_path: Path to the analyzed repository
            results: List of commit analysis results
            
        Returns:
            Dictionary with summary statistics
        """
        self._log("Generating summary statistics...")
        
        if not results:
            return self._empty_summary(repository_path)
        
        # Basic repository information
        summary = {
            'location': repository_path,
            'stat_of_repository': {            
                'analyzed_at': datetime.now().isoformat(),
                'number_of_commits': len(results),
                'avg_of_num_java_files':{'average_count': 0},
                'avg_of_num_warnings': {'average_count': 0}
            }
        }        
        
        # Calculate Java file statistics
        java_stats = self._calculate_java_statistics(results)
        summary['java_files'] = java_stats
        
        # Calculate PMD warning statistics
        warning_stats = self._calculate_warning_statistics(results)
        summary['warnings'] = warning_stats
        
        # Calculate temporal trends
        temporal_stats = self._calculate_temporal_trends(results)
        summary['temporal_trends'] = temporal_stats
        
        # Calculate rule-specific statistics
        rule_stats = self._calculate_rule_statistics(results)
        summary['rule_statistics'] = rule_stats
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(results)
        summary['quality_metrics'] = quality_metrics
        
        # Generate the required format from R8
        summary['formatted_summary'] = self._generate_formatted_summary(summary)
        
        return summary
    
    def _empty_summary(self, repository_path: str) -> Dict[str, Any]:
        """Generate empty summary for repositories with no results."""
        return {
            'location': repository_path,
            'stat_of_repository': {            
                'analyzed_at': datetime.now().isoformat(),
                'number_of_commits': len(results),
                'avg_of_num_java_files':{'average_count': 0},
                'avg_of_num_warnings': {'average_count': 0}
            },
            'java_files': {'average_count': 0},
            'warnings': {'average_count': 0},
            'warning_statistics': {},
            'formatted_summary': f'"location": "{repository_path}"\n"number_of_commits": 0\n"avg_of_num_java_files": 0\n"avg_of_num_warnings": 0\n"warning_statistics": {{}}'
        }
    
    def _calculate_java_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Java file statistics across all commits."""
        java_counts = [r['avg_of_num_java_files']['count'] for r in results]
        total_lines = [r['avg_of_num_java_files']['total_lines'] for r in results]
        
        return {
            'avg_of_num_java_files': statistics.mean(java_counts) if java_counts else 0,
            'median_count': statistics.median(java_counts) if java_counts else 0,
            'min_count': min(java_counts) if java_counts else 0,
            'max_count': max(java_counts) if java_counts else 0,
            'total_commits': len(java_counts),
            'average_total_lines': statistics.mean(total_lines) if total_lines else 0,
            'median_total_lines': statistics.median(total_lines) if total_lines else 0
        }
    
    def _calculate_warning_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate PMD warning statistics across all commits."""
        warning_counts = [r['pmd_analysis']['violation_count'] for r in results]
        files_with_violations = [r['pmd_analysis']['files_with_violations'] for r in results]
        
        # Collect all violations for detailed analysis
        all_violations = []
        for result in results:
            all_violations.extend(result['pmd_analysis']['violations'])
        
        # Count violations by priority
        priority_counts = Counter()
        for violation in all_violations:
            priority_counts[violation.get('priority', 0)] += 1
        
        return {
            'stat_of_warnings': statistics.mean(warning_counts) if warning_counts else 0,
            'median_count': statistics.median(warning_counts) if warning_counts else 0,
            'min_count': min(warning_counts) if warning_counts else 0,
            'max_count': max(warning_counts) if warning_counts else 0,
            'total_violations': sum(warning_counts),
            'average_files_with_violations': statistics.mean(files_with_violations) if files_with_violations else 0,
            'priority_distribution': dict(priority_counts)
        }
    
    def _calculate_temporal_trends(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate temporal trends in code quality."""
        # Sort results by timestamp
        sorted_results = sorted(results, key=lambda x: x['commit']['timestamp'])
        
        timestamps = [r['commit']['timestamp'] for r in sorted_results]
        java_counts = [r['java_files']['count'] for r in sorted_results]
        warning_counts = [r['pmd_analysis']['violation_count'] for r in sorted_results]
        
        # Calculate trends (simple linear trend)
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
        """Calculate statistics for each PMD rule."""
        rule_violations = defaultdict(int)
        rule_commits = defaultdict(set)
        
        for result in results:
            commit_hash = result['commit']['hash']
            for violation in result['pmd_analysis']['violations']:
                rule = violation.get('rule', 'Unknown')
                rule_violations[rule] += 1
                rule_commits[rule].add(commit_hash)
        
        # Convert to final format
        rule_stats = {}
        for rule, count in rule_violations.items():
            rule_stats[rule] = {
                'total_violations': count,
                'commits_affected': len(rule_commits[rule]),
                'average_per_commit': count / len(results) if results else 0
            }
        
        return rule_stats
    
    def _calculate_quality_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall quality metrics."""
        if not results:
            return {}
        
        # Calculate violation density (violations per 1000 lines)
        violation_densities = []
        for result in results:
            total_lines = result['java_files']['total_lines']
            violations = result['pmd_analysis']['violation_count']
            if total_lines > 0:
                density = (violations / total_lines) * 1000
                violation_densities.append(density)
        
        # Calculate file quality (percentage of files without violations)
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
    
    def _generate_formatted_summary(self, summary: Dict[str, Any]) -> str:
    repo_info = summary['repository']
    java_stats = summary['java_files']
    warning_stats = summary['warnings']
    rule_stats = summary['rule_statistics']
    
    stat_of_warnings = {rule: stats['total_violations'] for rule, stats in rule_stats.items()}
    
    formatted = f'"location": "{repo_info["location"]}"\n'
    formatted += '"stat_of_repository": {\n'
    formatted += f'    "number_of_commits": {repo_info["java_files"]},\n'
    formatted += f'    "avg_of_num_java_files": {java_stats["average_count"]:.1f},\n'
    formatted += f'    "avg_of_num_warnings": {warning_stats["average_count"]:.1f},\n'
    formatted += f'    "stat_of_warnings": {stat_of_warnings}\n'
    formatted += '}'
    
    return formatted

