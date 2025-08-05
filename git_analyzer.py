"""
Git Repository Analyzer
Handles Git repository operations including cloning, commit history retrieval, and file analysis.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
import git
from git import Repo, Commit
from tqdm import tqdm


class GitAnalyzer:
    """Analyzes Git repositories for commit history and file statistics."""
    
    def __init__(self, repository_path: str, verbose: bool = False):
        """
        Initialize GitAnalyzer.
        
        Args:
            repository_path: Path or URL to Git repository
            verbose: Enable verbose output
        """
        self.repository_path = repository_path
        self.verbose = verbose
        self.repo = None
        self.repo_path = None
        self.temp_dir = None
        self.is_cloned = False
        
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[GitAnalyzer] {message}")
    
    def _setup_repository(self):
        """Setup repository for analysis (clone if URL, or use local path)."""
        if self.repo is not None:
            return
            
        # Check if it's a URL or local path
        if self.repository_path.startswith(('http://', 'https://', 'git@')):
            # Clone remote repository
            self._log(f"Cloning repository from {self.repository_path}")
            self.temp_dir = tempfile.mkdtemp()
            self.repo_path = os.path.join(self.temp_dir, "repo")
            
            # Use shallow clone for better performance
            self.repo = Repo.clone_from(
                self.repository_path,
                self.repo_path,
                depth=None  # We need full history for commit analysis
            )
            self.is_cloned = True
            
        else:
            # Use local repository
            self._log(f"Using local repository at {self.repository_path}")
            self.repo_path = os.path.abspath(self.repository_path)
            
            if not os.path.exists(self.repo_path):
                raise ValueError(f"Repository path does not exist: {self.repo_path}")
            
            try:
                self.repo = Repo(self.repo_path)
            except git.exc.InvalidGitRepositoryError:
                raise ValueError(f"Invalid Git repository: {self.repo_path}")
    
    def get_commit_history(self, max_commits: Optional[int] = None) -> List[Commit]:
        """
        Get commit history from the repository.
        
        Args:
            max_commits: Maximum number of commits to retrieve
            
        Returns:
            List of Git commit objects
        """
        self._setup_repository()
        
        self._log("Retrieving commit history...")
        
        # Get all commits from all branches (focusing on main/master)
        try:
            # Try to use main branch first, then master
            if 'main' in self.repo.heads:
                commits = list(self.repo.iter_commits('main'))
            elif 'master' in self.repo.heads:
                commits = list(self.repo.iter_commits('master'))
            else:
                # Use current branch
                commits = list(self.repo.iter_commits())
        except Exception as e:
            self._log(f"Error getting commits: {e}")
            commits = list(self.repo.iter_commits())
        
        # Sort commits by date (oldest first for chronological analysis)
        commits.sort(key=lambda c: c.committed_date)
        
        if max_commits:
            commits = commits[:max_commits]
            
        self._log(f"Retrieved {len(commits)} commits")
        return commits
    
    def checkout_commit(self, commit: Commit):
        """
        Checkout a specific commit.
        
        Args:
            commit: Git commit object to checkout
        """
        self._log(f"Checking out commit {commit.hexsha[:8]}")
        
        try:
            self.repo.git.checkout(commit.hexsha, force=True)
        except Exception as e:
            self._log(f"Warning: Could not checkout commit {commit.hexsha[:8]}: {e}")
            # Continue with current state
    
    def count_java_files(self) -> dict:
        """
        Count Java files in the current repository state.
        
        Returns:
            Dictionary with Java file statistics
        """
        java_files = []
        total_lines = 0
        
        repo_path = Path(self.repo_path)
        
        # Find all .java files
        for java_file in repo_path.rglob("*.java"):
            try:
                # Skip files in common non-source directories
                if any(part in java_file.parts for part in ['.git', 'target', 'build', 'bin']):
                    continue
                    
                # Count lines in file
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                
                java_files.append({
                    'path': str(java_file.relative_to(repo_path)),
                    'lines': lines
                })
                total_lines += lines
                
            except Exception as e:
                self._log(f"Warning: Could not process {java_file}: {e}")
                continue
        
        return {
            'count': len(java_files),
            'files': java_files,
            'total_lines': total_lines
        }
    
    def get_commit_info(self, commit: Commit) -> dict:
        """
        Get detailed information about a commit.
        
        Args:
            commit: Git commit object
            
        Returns:
            Dictionary with commit information
        """
        return {
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
            'message': commit.message.strip(),
            'stats': {
                'files_changed': len(commit.stats.files),
                'insertions': commit.stats.total['insertions'],
                'deletions': commit.stats.total['deletions']
            }
        }
    
    def cleanup(self):
        """Clean up temporary resources."""
        if self.is_cloned and self.temp_dir and os.path.exists(self.temp_dir):
            self._log("Cleaning up temporary directory")
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                self._log(f"Warning: Could not clean up temp directory: {e}")
