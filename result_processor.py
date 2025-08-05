"""
Result Processor
Processes PMD analysis results and generates JSON output for each commit.
"""

from typing import Dict, Any
from datetime import datetime
from git import Commit


class ResultProcessor:
    """Processes and formats analysis results."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize ResultProcessor.
        
        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
    
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[ResultProcessor] {message}")
    
    def process_commit_result(self, commit: Commit, java_files: Dict, pmd_result: Dict) -> Dict[str, Any]:
        """
        Process results for a single commit.
        
        Args:
            commit: Git commit object
            java_files: Java file statistics
            pmd_result: PMD analysis results
            
        Returns:
            Dictionary with processed commit results
        """
        self._log(f"Processing results for commit {commit.hexsha[:8]}")
        
        # Basic commit information
        commit_info = {
            'hash': commit.hexsha,
            'short_hash': commit.hexsha[:8],
            'author': {
                'name': commit.author.name,
                'email': commit.author.email
            },
            'committer': {
                'name': commit.committer.name,
                'email': commit.committer.email
            },
            'date': commit.committed_datetime.isoformat(),
            'timestamp': commit.committed_date,
            'message': commit.message.strip(),
            'stats': {
                'files_changed': len(commit.stats.files),
                'insertions': commit.stats.total['insertions'],
                'deletions': commit.stats.total['deletions']
            }
        }
        
        # Java files information
        java_info = {
            'count': java_files['count'],
            'total_lines': java_files['total_lines'],
            'files': java_files['files']
        }
        
        # PMD analysis results
        pmd_info = {
            'violation_count': pmd_result['violation_count'],
            'files_with_violations': pmd_result['files_with_violations'],
            'rules_violated': pmd_result['rules_violated'],
            'violations': pmd_result['violations']
        }
        
        # Calculate additional statistics
        stats = self._calculate_statistics(java_info, pmd_info)
        
        return {
            'commit': commit_info,
            'java_files': java_info,
            'pmd_analysis': pmd_info,
            'statistics': stats,
            'processed_at': datetime.now().isoformat()
        }
    
    def _calculate_statistics(self, java_info: Dict, pmd_info: Dict) -> Dict[str, Any]:
        """
        Calculate additional statistics from the analysis results.
        
        Args:
            java_info: Java file information
            pmd_info: PMD analysis information
            
        Returns:
            Dictionary with calculated statistics
        """
        java_count = java_info['count']
        total_lines = java_info['total_lines']
        violation_count = pmd_info['violation_count']
        files_with_violations = pmd_info['files_with_violations']
        
        # Calculate ratios and averages
        stats = {
            'violations_per_file': violation_count / java_count if java_count > 0 else 0,
            'violations_per_1000_lines': (violation_count / total_lines * 1000) if total_lines > 0 else 0,
            'files_with_violations_ratio': files_with_violations / java_count if java_count > 0 else 0,
            'average_lines_per_file': total_lines / java_count if java_count > 0 else 0
        }
        
        # Violation severity distribution
        violation_by_priority = {}
        for violation in pmd_info['violations']:
            priority = violation.get('priority', 0)
            violation_by_priority[priority] = violation_by_priority.get(priority, 0) + 1
        
        stats['violation_by_priority'] = violation_by_priority
        
        # Rule violation frequency
        rule_frequency = {}
        for rule in pmd_info['rules_violated']:
            rule_count = sum(1 for v in pmd_info['violations'] if v.get('rule') == rule)
            rule_frequency[rule] = rule_count
        
        stats['rule_frequency'] = rule_frequency
        
        # File-level statistics
        file_violation_stats = {}
        for violation in pmd_info['violations']:
            filename = violation.get('file', '')
            if filename not in file_violation_stats:
                file_violation_stats[filename] = {
                    'violation_count': 0,
                    'rules': set()
                }
            file_violation_stats[filename]['violation_count'] += 1
            file_violation_stats[filename]['rules'].add(violation.get('rule', ''))
        
        # Convert sets to lists for JSON serialization
        for filename, file_stats in file_violation_stats.items():
            if isinstance(file_stats['rules'], set):
                file_stats['rules'] = list(file_stats['rules'])
            file_stats['unique_rules'] = len(file_stats['rules'])
        
        stats['file_violation_stats'] = file_violation_stats
        
        return stats
