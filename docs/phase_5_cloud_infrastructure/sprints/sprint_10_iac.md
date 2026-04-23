# Sprint 10: Infrastructure as Code (IaC) & SSO

**Goal:** Establish theoretical proof-of-capability for deploying the architecture into a multi-tenant enterprise boundary. Emulate the Cloud Load Balancer and AWS Cognito integration strictly via documentation and IaC manifests.

## 🎯 Deliverables

1. **Infrastructure Documentation:** 
   - Create `infrastructure/aws_ecs_deployment.yml`.
   - Map exactly how the Application Load Balancer routes traffic to the target groups on `8501`.
   - Map how AWS Cognito intercepts unauthorized endpoints at the ALB listener level before it hits Streamlit.

## ✅ Definition of Done
- A strictly formatted CloudFormation/Infrastructure document exists that proves the architectural viability.
