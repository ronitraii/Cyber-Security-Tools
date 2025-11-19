# Ransomware Simulation Tool - Week 11

## 📋 Overview

This is an educational ransomware simulation tool developed as part of a cybersecurity internship. The tool demonstrates how ransomware operates by encrypting and decrypting files in a controlled, safe environment.

**⚠️ IMPORTANT: This tool is for EDUCATIONAL PURPOSES ONLY**

## 🎯 Objectives

- Understand ransomware attack patterns and behavior
- Learn about file encryption and cryptographic operations
- Develop security awareness and incident response knowledge
- Demonstrate technical capabilities in a cybersecurity context

## 🔧 Features

### Core Functionality
- ✅ **Safe Simulation Mode**: Creates encrypted copies without destroying originals
- ✅ **Symmetric Encryption**: Uses Fernet (AES-128) for file encryption
- ✅ **Key Management**: Secure key generation and storage
- ✅ **File Scanning**: Intelligent file targeting with safety exclusions
- ✅ **Logging System**: Comprehensive activity tracking and audit trails
- ✅ **Recovery Mode**: Complete decryption and file restoration
- ✅ **Analysis Reports**: Detailed technical and statistical reports

### Safety Mechanisms
- Default simulation mode (non-destructive)
- Protected file type exclusions (.exe, .dll, .sys, .py)
- Test directory creation with sample files
- Confirmation required for real mode
- Comprehensive error handling

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Setup Steps

1. **Install Required Packages**
   ```powershell
   pip install cryptography
   ```

2. **Verify Installation**
   ```powershell
   python --version
   pip list | Select-String cryptography
   ```

## 🚀 Usage

### Basic Commands

#### 1. Complete Demo (Recommended for First Run)
```powershell
python "Ransomare tool.py" --mode demo
```
This runs a full demonstration: encryption → ransom note → decryption → analysis

#### 2. Encryption Simulation
```powershell
python "Ransomare tool.py" --mode encrypt
```

#### 3. Decryption Recovery
```powershell
python "Ransomare tool.py" --mode decrypt --key "Week 11/encryption_key_XXXXXXXX.key"
```

#### 4. Generate Analysis Report
```powershell
python "Ransomare tool.py" --mode analyze
```

#### 5. Custom Target Directory
```powershell
python "Ransomare tool.py" --mode encrypt --target "Week 11/CustomTest"
```

### Advanced Options

```powershell
# View all available options
python "Ransomare tool.py" --help

# Real mode (DANGEROUS - not recommended)
python "Ransomare tool.py" --mode encrypt --real-mode
```

## 📊 Output Files

After running the tool, you'll find the following files in the `Week 11/` directory:

| File | Description |
|------|-------------|
| `encryption_key_XXXXXXXX.key` | Encryption key for recovery |
| `attack_report_XXXXXXXX.json` | Detailed JSON attack statistics |
| `analysis_report_XXXXXXXX.txt` | Comprehensive analysis report |
| `Logs/ransomware_sim_XXXXXXXX.log` | Complete activity log |
| `TestFiles/` | Sample files for simulation |
| `TestFiles/RANSOM_NOTE.txt` | Simulated ransom note |

## 🔍 Technical Details

### Encryption Algorithm
- **Algorithm**: Fernet (symmetric encryption)
- **Key Derivation**: PBKDF2-HMAC-SHA256
- **Cipher**: AES-128-CBC with HMAC authentication
- **Implementation**: Python `cryptography` library

### Attack Chain Phases
1. **Reconnaissance**: Scan target directory for vulnerable files
2. **Key Generation**: Create strong encryption key
3. **Encryption**: Encrypt files with progress tracking
4. **Notification**: Deploy ransom note
5. **Logging**: Record all activities

### File Flow
```
Original File → Scan → Encrypt → .encrypted → Decrypt → Restored File
```

## 🛡️ Security Considerations

### What This Tool Demonstrates
- How ransomware encrypts files
- The importance of backups
- Impact of cryptographic attacks
- Recovery challenges without keys

### Protection Strategies
1. **Prevention**
   - Regular, isolated backups
   - Keep systems updated
   - Use endpoint protection
   - Email filtering and awareness

2. **Detection**
   - File integrity monitoring
   - Behavioral analysis
   - Anomaly detection

3. **Response**
   - Incident response plan
   - Network isolation
   - Forensic analysis
   - Backup restoration

## 📈 Use Cases for Internship Report

### 1. Technical Demonstration
- Shows understanding of cryptography
- Demonstrates Python programming skills
- Exhibits security tool development

### 2. Analysis Skills
- Threat modeling and attack simulation
- Log analysis and forensics
- Risk assessment documentation

### 3. Security Awareness
- Understanding attack vectors
- Mitigation strategy development
- Incident response planning

## 📸 Screenshots for Report

Recommended screenshots to include:
1. Tool execution with encryption progress
2. Ransom note display
3. Decryption recovery process
4. Log file contents
5. Analysis report output
6. File comparison (before/after)

## 🧪 Testing Checklist

- [ ] Tool runs without errors
- [ ] Test files are created automatically
- [ ] Encryption creates .encrypted files
- [ ] Decryption restores original content
- [ ] Log files are generated
- [ ] Analysis reports are created
- [ ] Ransom note is deployed
- [ ] Key file is saved properly

## 📝 Report Documentation Template

```markdown
## Ransomware Simulation Tool

### Objective
Develop a functional ransomware simulation tool to understand attack 
patterns and strengthen defensive strategies.

### Implementation
- Programming Language: Python 3
- Libraries: cryptography, logging, pathlib
- Architecture: Object-oriented with safety mechanisms

### Features
[List key features from above]

### Results
- Successfully encrypted X test files in Y seconds
- Demonstrated complete attack-recovery cycle
- Generated comprehensive logs and reports

### Security Insights
[Discuss findings and mitigation strategies]

### Conclusion
This project enhanced my understanding of ransomware mechanics and 
defensive cybersecurity measures.
```

## ⚖️ Legal and Ethical Considerations

**CRITICAL WARNINGS:**
- Only use on systems you own or have explicit permission to test
- Never deploy on production systems or networks
- Do not use for malicious purposes
- Unauthorized use may violate computer fraud laws
- This tool is for learning and demonstration only

## 🤝 Credits

- **Project**: Cybersecurity Internship - Week 11
- **Purpose**: Educational demonstration and security awareness
- **Date**: November 2025
- **Framework**: Python with cryptography library

## 📚 Further Learning

### Recommended Topics
- Cryptography fundamentals
- Incident response procedures
- Backup and disaster recovery
- Network security monitoring
- Threat intelligence analysis

### Resources
- NIST Cybersecurity Framework
- MITRE ATT&CK Framework (Ransomware tactics)
- OWASP Security Guidelines
- Python Cryptography Documentation

## 🐛 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'cryptography'`
**Solution**: Run `pip install cryptography`

**Issue**: Permission denied errors
**Solution**: Run PowerShell/Terminal as administrator

**Issue**: No files found to encrypt
**Solution**: Tool automatically creates test files - check `Week 11/TestFiles/`

**Issue**: Decryption fails
**Solution**: Ensure you're using the correct key file from the same session

## 📞 Support

For questions or issues related to this educational project:
- Review the log files in `Week 11/Logs/`
- Check the analysis reports for detailed information
- Verify all prerequisites are installed correctly

---

**Remember**: This is a learning tool. Real ransomware causes serious harm. 
Always practice ethical cybersecurity and protect systems, not exploit them.
