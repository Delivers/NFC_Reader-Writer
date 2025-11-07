# 🪪 NTAG215 NFC URL Writer & Reader

A lightweight Python 3 tool that writes a **URL (NDEF record)** to **NTAG215 NFC tags** using a supported USB NFC reader (such as an ACR122U).  
This version **does not require or set any password** on the tag — it simply writes the Tag UID and provided URL or reads when a tag is detected.
**It was tested with NFC tag Type4 / ntag215 and need do be teste with Type5 !!!**

---

## ✨ Features

- 🔹 Writes any URL to an NTAG215 (or compatible) NFC tag 
- 🔹 Reads the UID of the tag
- 🔹 Formats it as hex without spaces, e.g. 04A2B3C4D5E6F7
- 🔹 Appends it to the URL as a query parameter:
- 🔹 Automatically encodes URLs as **NDEF UriRecords** 
- 🔹 **`https://example.com → https://example.com?uid=04A2B3C4D5E6F7`**
- 🔹 Detects cards dynamically via `pyscard`  
- 🔹 Simple command-line interface using `argparse`  
- 🔹 Optionally available as a **compiled Windows executable** (`NFC_Writer.exe`)  
- 🔹 Prints detailed status for each write operation  

---

## 🧰 Requirements (for Python users)

- **Python 3.8+** (tested with Python 3.10 and 3.11)
- A supported **NFC reader** (e.g. ACR122U)
- An **NTAG215** or compatible NFC tag

### 🧩 Install dependencies

Install all dependencies with:

```bash
pip install -r requirements.txt
```
- or manualy
```bash
pip install pyscard
pip install ndeflib
pip install python-dotenv
```

---

## ⚙️ Usage

Run the script and pass in the URL you want to write:

```bash
python3 NFC_Writer.py "https://example.com"
```
---

## 🛠️ Compile

Run the command to compile in pyhon to .exe:

```bash
pip install pyinstaller
pyinstaller --onefile --icon=data.ico NFC_Writer.py
```
---

## 💻 Run compiled version (Windows)

A precompiled binary, dist/NFC_Writer.exe, is included in this repository.
You can run it directly from the command line — no Python installation required:

```bash
NFC_Writer.exe "https://example.com"
```
Then place an NFC tag on your reader.
The URL will be written automatically once the tag is detected.

---

## Example Output

```yaml
Present a tag to the reader.
Press Enter to stop...
https://example.com?uid=04A1CCB1320289
https://example.com?uid=04A1CCB1320289
```
To stop the script, press Enter.

## 🧩 File Structure

```yaml

Dataland_NFC_Reader-Writer/
│
├── NFC_Writer.py      # Main NFC writing script (Python)
├── dist/NFC_Writer.exe      # Precompiled Windows executable for writing
├── NFC_Reader.py      # Main NFC reading script (Python)
├── dist/NFC_Reader.exe      # Precompiled Windows executable for reading
├── README.md           # Documentation
└── requirements.txt    # Python dependencies

```

## 🧲 NFC Reader Driver (Windows)

If your ACR122U reader is not automatically recognized, you can install the official driver from ACS.
The latest Windows drivers are available here:


[👉 ACR122U Windows Driver (Gototags GitLab)](https://gitlab.com/gototags/public/-/tree/main/NFC/Readers/ACS/drivers/windows)


## 📜 License

This project is licensed under the MIT License — feel free to modify and distribute.






