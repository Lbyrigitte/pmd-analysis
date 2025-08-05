"""
PMD Runner
Handles PMD download, installation, and execution for static analysis.
"""

import os
import sys
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Optional
import requests
from tqdm import tqdm


class PMDRunner:
    """Manages PMD static analysis tool execution."""
    
    def __init__(self, version: str = "7.15.0", skip_download: bool = False, verbose: bool = False, pmd_path: str = None):
        """
        Initialize PMDRunner.

        Args:
            version: PMD version to use
            skip_download: Skip download if PMD already exists
            verbose: Enable verbose output
            pmd_path: Path to existing PMD installation (optional)
        """
        self.version = version
        self.skip_download = skip_download
        self.verbose = verbose
        self.pmd_path = pmd_path
        self.pmd_home = None
        self.pmd_bin = None
        
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[PMDRunner] {message}")
    
    def _download_pmd(self) -> str:
        """
        Download PMD if not already present.
        
        Returns:
            Path to PMD installation directory
        """
        pmd_dir = Path("./pmd")
        pmd_dir.mkdir(exist_ok=True)
        
        pmd_install_dir = pmd_dir / f"pmd-bin-{self.version}"
        
        if self.skip_download and pmd_install_dir.exists():
            self._log(f"Using existing PMD installation at {pmd_install_dir}")
            return str(pmd_install_dir)
        
        # Download PMD - try multiple URLs
        download_urls = [
            f"https://github.com/pmd/pmd/releases/download/pmd_releases%2F{self.version}/pmd-bin-{self.version}.zip",
            f"https://github.com/pmd/pmd/releases/download/pmd_releases/{self.version}/pmd-bin-{self.version}.zip",
            f"https://github.com/pmd/pmd/releases/download/v{self.version}/pmd-bin-{self.version}.zip"
        ]
        zip_path = pmd_dir / f"pmd-bin-{self.version}.zip"
        
        # Try multiple download URLs
        response = None
        successful_url = None

        for download_url in download_urls:
            self._log(f"Trying to download PMD {self.version} from {download_url}")
            try:
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                successful_url = download_url
                break
            except requests.exceptions.RequestException as e:
                self._log(f"Failed to download from {download_url}: {e}")
                continue

        if response is None or successful_url is None:
            raise RuntimeError(f"Failed to download PMD {self.version} from any of the attempted URLs")

        self._log(f"Successfully downloading PMD {self.version} from {successful_url}")

        try:
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(zip_path, 'wb') as f:
                if total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading PMD") as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            # Extract PMD
            self._log("Extracting PMD...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(pmd_dir)
            
            # Clean up zip file
            zip_path.unlink()
            
            self._log(f"PMD installed to {pmd_install_dir}")
            return str(pmd_install_dir)
            
        except Exception as e:
            raise RuntimeError(f"Failed to download PMD: {e}")
    
    def setup(self):
        """Setup PMD for execution."""
        # Check Java availability first
        self._check_java()

        # Use provided PMD path or download PMD
        if self.pmd_path and os.path.exists(self.pmd_path):
            self._log(f"Using provided PMD installation at {self.pmd_path}")
            self.pmd_home = self.pmd_path
        else:
            self.pmd_home = self._download_pmd()

        # Determine PMD binary path based on OS
        if sys.platform.startswith('win'):
            self.pmd_bin = os.path.join(self.pmd_home, "bin", "pmd.bat")
        else:
            self.pmd_bin = os.path.join(self.pmd_home, "bin", "pmd")

        if not os.path.exists(self.pmd_bin):
            raise RuntimeError(f"PMD binary not found at {self.pmd_bin}")

        # Make binary executable on Unix systems
        if not sys.platform.startswith('win'):
            os.chmod(self.pmd_bin, 0o755)

        self._log(f"PMD setup complete. Binary: {self.pmd_bin}")

    def _check_java(self):
        """Check if Java is available and get version."""
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise RuntimeError("Java command failed")

            # Java version info is typically in stderr
            version_info = result.stderr or result.stdout
            self._log(f"Java version check: {version_info.split()[0] if version_info else 'Unknown'}")

        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            raise RuntimeError(
                f"Java is not available or not in PATH. Please install Java 11+ and ensure it's in PATH. Error: {e}"
            )
    
    def run_analysis(self, source_path: str, ruleset_path: str) -> Dict:
        """
        Run PMD analysis on source code.
        
        Args:
            source_path: Path to source code directory
            ruleset_path: Path to PMD ruleset file
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.pmd_bin:
            raise RuntimeError("PMD not setup. Call setup() first.")
        
        # Create temporary file for PMD output
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.xml', delete=False) as temp_file:
            output_file = temp_file.name
        
        try:
            # Build PMD command (PMD 7.x uses 'check' subcommand)
            cmd = [
                self.pmd_bin,
                "check",
                "-d", source_path,
                "-R", ruleset_path,
                "-f", "xml",
                "-r", output_file,
                "--no-cache",
                "--fail-on-violation=false"  # Don't fail due to violations, only fail due to real mistakes
            ]
            
            self._log(f"Running PMD: {' '.join(cmd)}")
            
            # Run PMD
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            self._log(f"PMD exit code: {result.returncode}")
            if result.stdout:
                self._log(f"PMD stdout: {result.stdout}")
            if result.stderr:
                self._log(f"PMD stderr: {result.stderr}")

            # PMD returns non-zero exit code when violations are found
            # This is expected behavior, so we don't treat it as an error
            # Exit code 0: No violations found
            # Exit code 4: Violations found (this is normal)
            # Exit code 5: Processing errors (but may still have partial results)
            # Exit codes > 5: Real fatal errors
            if result.returncode > 5:
                error_msg = f"PMD execution failed with code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nStderr: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nStdout: {result.stdout}"
                raise RuntimeError(error_msg)
            elif result.returncode == 5:
                # Log warning but continue - PMD may have partial results
                self._log(f"Warning: PMD encountered processing errors (exit code 5) but continuing with partial results")
                if result.stderr:
                    self._log(f"PMD stderr: {result.stderr}")
                if result.stdout:
                    self._log(f"PMD stdout: {result.stdout}")

            # Parse PMD output
            return self._parse_pmd_output(output_file)
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("PMD execution timed out")
        except Exception as e:
            raise RuntimeError(f"PMD execution failed: {e}")
        finally:
            # Clean up temporary file
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def _parse_pmd_output(self, output_file: str) -> Dict:
        """
        Parse PMD XML output.
        
        Args:
            output_file: Path to PMD XML output file
            
        Returns:
            Dictionary with parsed results
        """
        import xml.etree.ElementTree as ET
        
        try:
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                return {
                    'violations': [],
                    'violation_count': 0,
                    'files_with_violations': 0,
                    'rules_violated': []
                }
            
            tree = ET.parse(output_file)
            root = tree.getroot()

            violations = []
            files_with_violations = set()
            rules_violated = set()

            # Handle XML namespace
            namespace = {'pmd': 'http://pmd.sourceforge.net/report/2.0.0'}

            # Find file elements with namespace
            file_elements = root.findall('.//pmd:file', namespace) if root.tag.startswith('{') else root.findall('file')

            for file_elem in file_elements:
                filename = file_elem.get('name', '')

                # Find violation elements with namespace
                violation_elements = file_elem.findall('.//pmd:violation', namespace) if root.tag.startswith('{') else file_elem.findall('violation')

                for violation in violation_elements:
                    violation_data = {
                        'file': filename,
                        'line': int(violation.get('beginline', 0)),
                        'column': int(violation.get('begincolumn', 0)),
                        'end_line': int(violation.get('endline', 0)),
                        'end_column': int(violation.get('endcolumn', 0)),
                        'rule': violation.get('rule', ''),
                        'ruleset': violation.get('ruleset', ''),
                        'priority': int(violation.get('priority', 0)),
                        'message': violation.text.strip() if violation.text else ''
                    }
                    
                    violations.append(violation_data)
                    files_with_violations.add(filename)
                    rules_violated.add(violation.get('rule', ''))
            
            return {
                'violations': violations,
                'violation_count': len(violations),
                'files_with_violations': len(files_with_violations),
                'rules_violated': list(rules_violated)
            }
            
        except ET.ParseError as e:
            self._log(f"Warning: Could not parse PMD output: {e}")
            return {
                'violations': [],
                'violation_count': 0,
                'files_with_violations': 0,
                'rules_violated': [],
                'parse_error': str(e)
            }
        except Exception as e:
            self._log(f"Warning: Error processing PMD output: {e}")
            return {
                'violations': [],
                'violation_count': 0,
                'files_with_violations': 0,
                'rules_violated': [],
                'error': str(e)
            }
