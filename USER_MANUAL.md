# 💃 Dance Academy Management System - User Manual

Welcome to the **Dance Academy Management System**. This guide provides a comprehensive overview of the features and tools available to help you manage your academy efficiently.

---

## 🚀 1. Getting Started
- **URL**: `http://127.0.0.1:5000` (Local Host)
- **Primary Admin**: `admin` / `admin123`
- **Dashboard**: A quick overview of Active Students, Monthly Income, Pending Balances, and Recent Activity.

---

## 👥 2. Student Management
The heart of the system.
- **Profiles**: Store student names, 10-digit phone numbers, and optional profile photos.
- **Status Tracking**: Mark students as 'Active' or 'Inactive'. Only active students are billed monthly.
- **Admission Logic**:
    - **Initial Charge**: Automatically charged when a student is added.
    - **Admission Types**:
        - **Normal**: Standard fee (set in Settings).
        - **Scholarship**: 100% discount.
        - **Percentage**: Custom discount applied to the base fee.
    - **Annual Renewal**: Admissions must be renewed annually. Use the "Renew Annual Admissions" button in the Finance section to scan and charge due students.
    - **Re-admission**: If a student is reactivated (Inactive -> Active), the system can charge a 50% re-admission fee.
- **Enrollment**: Easily enroll students into specific classes.

---

## 🎭 3. Special Events & Workshops
Manage short-term programs for everyone.
- **Internal Students**: Academy students can enroll directly. Charges are added to their ledger.
- **External Guests**: Host students from outside. The system tracks their name/phone separately without creating a full student profile.
- **One-time Fees**: Workshop fees are handled as single transactions, separate from monthly tuition.

---

## 📦 4. Membership Packages
Long-term plans for committed students.
- **Duration**: Create packages (e.g., 3-month or 6-month) with a fixed total price.
- **Admission Requirement**: Enrollment is only allowed if the student has paid their admission fee.
- **Payment Deadlines**: Set a deadline for final payments (e.g., 50% or more must be cleared within a certain period).

---

## 💰 5. Financial Ledger (Accounting)
Standardized accounting ensures no data is ever lost.
- **Monthly Billing**: Generate fees for all active students with one click.
- **Admission Renewals**: New "Renew Annual Admissions" button to handle yearly fees.
- **Advance Payments**: The ledger handles advance payments automatically.
- **Payment History**: A complete, unchangeable list of every bill and payment.
- **Void Logic**: Transactions are "Voided" rather than deleted for audit trails.
- **Permanent Deletion (Admin Only)**: Admin has the power to permanently delete records using the trash icon (🗑️).
- **Receipts**: Generate professional A4-ready PDF-style receipts.

---

## 👕 6. Clothing & Academy Shop
Sell academy branding directly to your students.
- **Inventory Management**: Track stock levels for T-shirts, hoodies, and other merch.
- **Discounting**: Adjust the final sold price during checkout to apply custom discounts to specific students.
- **Ledger Integration**: All purchases are automatically billed to the student's personal financial ledger.

---

## 💸 7. Expense Management
Track where your money goes.
- **Categories**: Record utility bills, rent, or 'Salary'.
- **Salary Tracking**: Link expenses to specific instructors to keep track of payroll history.

---

## 📊 6. Reports & Analytics
Data-driven insights for your academy.
- **Defaulters List**: Instantly see who owes money and how much.
- **Income/Expense Summary**: View your net profit for any specific date range.
- **CSV Export**: Download your Finance, Attendance, or Income data into Excel-compatible files for external record-keeping.

---

## 🛡️ 7. User Access & Security
Control who can see what.
- **Checkbox Permissions**: As an Admin, you can create accounts for your staff and choose exactly which features they can access (e.g., allow them to take attendance but hide the financial ledger).
- **Permission Badges**:
    - **S**: Students
    - **C**: Classes 
    - **A**: Attendance
    - **F**: Finance
    - **E**: Expenses
    - **R**: Reports
    - **P**: Settings
- **Password Security**: Users can change their passwords from the sidebar. Passwords must be 8+ characters with a mix of letters and numbers.

---

## ⚙️ 8. System Settings
Customized for your brand.
- **Academy Details**: Update your Academy Name, Address, and Contact info.
- **Custom Logo**: Upload your logo to appear on the dashboard and student receipts.

---

*For support or technical issues, please contact your system administrator.*
