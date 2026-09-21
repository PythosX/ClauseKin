# 🔎 ContractLens

### AI-Powered Business Contract Intelligence & Obligation Tracking

ContractLens is an **AI-powered contract intelligence platform** designed to transform business contracts from static documents into structured, actionable information.

It helps users understand contracts, extract important terms, identify obligations and deadlines, ask questions about agreements, and compare contract versions — reducing the manual effort required to monitor business contracts.

---

## 🎯 Problem

Business contracts often contain critical information such as:

* Payment terms
* Expiry dates
* Renewal conditions
* Termination clauses
* Party obligations
* Deadlines
* Important operational requirements

When businesses manage multiple contracts, manually finding and tracking this information can become time-consuming and easy to overlook.

**ContractLens addresses this problem by using AI to analyze contracts and organize the important information into a usable interface.**

---

## 💡 Solution

ContractLens follows an AI-powered workflow:

```text
📄 Upload Contract
        ↓
🔍 Extract Content
        ↓
🤖 AI Analysis
        ↓
🧠 Understand Contract
        ↓
📊 Structured Information
        ↓
📌 Obligations & Deadlines
        ↓
💬 Contract Q&A
        ↓
⚡ Actionable Insights
```

---

## ✨ Key Features

### 📄 Contract Upload

Upload business contracts and process them through the ContractLens analysis pipeline.

Supported formats include:

* PDF
* DOCX
* TXT

### 🧠 AI Contract Analysis

Automatically identify important contract information:

* Parties
* Effective date
* Expiry date
* Renewal terms
* Payment terms
* Termination conditions
* Contract summary

### 📌 Obligation Tracking

Extract obligations from contracts and organize them based on:

* Responsible party
* Obligation
* Deadline
* Frequency
* Risk
* Source section/page

### 💬 Contract AI Chat

Ask questions about a specific contract using natural language.

Example:

> "When does this contract expire?"

> "What are the renewal conditions?"

> "What obligations does the vendor have?"

### 🔄 Contract Comparison

Compare different contract versions and identify changes in important terms.

### 📊 Contract Dashboard

Monitor contracts and access important information through a centralized dashboard.

### ⏳ Background Processing

Contract analysis runs through a background processing workflow with status stages such as:

```text
Queued
  ↓
Extracting
  ↓
Analyzing
  ↓
Completed
```

This prevents the interface from appearing frozen during larger document processing.

### 🔐 Demo Login

ContractLens currently includes a demo login flow for the prototype.

```text
Email: demo@contractlens.ai
Password: demo123
```

> The current authentication is intended for the hackathon/demo environment and is not production-grade authentication.

---

## 🤖 Agentic AI Concept

ContractLens is designed around an agentic workflow rather than simply generating a contract summary.

```text
OBSERVE
   ↓
EXTRACT
   ↓
REASON
   ↓
IDENTIFY IMPORTANT EVENTS
   ↓
RECOMMEND ACTION
   ↓
HUMAN APPROVAL
   ↓
ACTION
   ↓
RECORD RESULT
```

The long-term vision is for ContractLens to help businesses move from:

**"What does this contract say?"**

to:

**"What do I need to know and what should I do next?"**

---

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │      User           │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ HTML/CSS/JS Frontend│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    FastAPI Backend  │
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
        ┌────────────┐  ┌────────────┐  ┌────────────┐
        │ Document   │  │ Gemini AI  │  │  SQLite    │
        │ Processing │  │ Analysis   │  │  Database  │
        └────────────┘  └────────────┘  └────────────┘
                │              │              │
                └──────────────┼──────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Contract Intelligence│
                    └─────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        Obligations        AI Q&A          Comparison
```

---

## 🛠️ Tech Stack

| Technology     | Purpose                      |
| -------------- | ---------------------------- |
| **HTML**       | Frontend structure           |
| **CSS**        | UI and responsive design     |
| **JavaScript** | Frontend interactions        |
| **Python**     | Backend development          |
| **FastAPI**    | API and backend server       |
| **SQLite**     | Contract/data storage        |
| **Gemini API** | AI-powered contract analysis |
| **Docling**    | Document parsing             |
| **Render**     | Deployment                   |

---

## 🏆 Hackathon

ContractLens was developed as part of the:

**Agentic AI Hackathon — conducted by Product Space**

The project focuses on demonstrating how an AI agent can move beyond document summarization toward **understanding contracts, identifying important events, and helping users decide what actions need attention.**

---

## ⚠️ Disclaimer

ContractLens is a **technical prototype for contract intelligence and workflow assistance**.

It is not intended to provide legal advice or replace qualified legal professionals.

---

## 👨‍💻 Built With

**Python • FastAPI • JavaScript • SQLite • Gemini AI • Docling • HTML/CSS**

> **ContractLens — Turn contracts into information you can understand, track, and act on.**
