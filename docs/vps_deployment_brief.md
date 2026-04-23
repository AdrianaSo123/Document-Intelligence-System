# Deployment Strategy Brief: Cloud Virtual Private Server (VPS)

## 1. Executive Summary
This document outlines the proposed production deployment strategy for the Business Document Intelligence System (BDIS). We will circumvent the high costs of fully-managed AWS infrastructure while strictly maintaining our enterprise microservice patterns by utilizing a single $5/month Linux Virtual Private Server. 

## 2. Why the VPS Route?
*   **Cost-Effective:** A fixed $5/month compared to variable AWS bills ($50+ for Load Balancers and managed RDS).
*   **Zero Architectural Compromise:** Preserves the existing `docker-compose.yml` flawlessly without having to "Frankenstein" multiple free-tiers across the internet.
*   **Resume Impact:** Demonstrates raw Linux server administration and Docker orchestration skills—highly coveted by Senior Engineering teams.

## 3. The Implementation Blueprint (Next Session)
When we are ready to deploy, we will execute the following sequentially:
1.  **Server Provisioning:** Rent an Ubuntu 22.04 LTS instance via DigitalOcean or Linode.
2.  **Environment Setup:** SSH into the server and securely install the Docker runtime.
3.  **Code Transfer:** Clone the central GitHub repository natively onto the remote Linux server.
4.  **Orchestration:** Run `docker compose up -d --build`. The server will dynamically partition itself to run the Database, Message Broker, API Backend, and Streamlit Frontend containers simultaneously.

## 4. Required Materials
Before we deploy during our next session, ensure you have the following ready:
*   An active GitHub repository hosting this up-to-date codebase.
*   A DigitalOcean/Linode account (Note: DigitalOcean often offers $200 in free credits for new developers).
