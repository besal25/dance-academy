# 🎭 Dance Academy Management System

A comprehensive web-based management system for dance academies, built with Flask and modern web technologies. This system streamlines academy operations including student management, class scheduling, attendance tracking, financial management, and reporting.

## ✨ Features

### 👥 Student Management
- Complete student profiles with photos
- Flexible admission fee options (Normal, Scholarship, Percentage Discount, Fixed Amount)
- Custom monthly fees per student
- Student status tracking (Active/Inactive)
- Progress reports and performance tracking
- Re-admission with automatic 50% fee discount
- Bulk delete functionality (Admin only)

### 📚 Class & Instructor Management
- Create and manage multiple classes
- Assign instructors to classes
- Student enrollment tracking
- Class schedules and capacity management

### ✅ Attendance System
- Quick attendance marking interface
- Date-wise attendance tracking
- Student attendance history
- Attendance reports

### 💰 Advanced Financial Management
- **Ledger-based accounting system**
- Student-wise financial tracking
- Advance payment support
- Automatic monthly fee generation
- **Package Protection**: Prevents double billing when students enroll in packages
- **Workshop Fee Waiver**: Optional monthly fee waiver during workshop enrollment
- Transaction voiding and balance recalculation
- Payment receipts with print functionality
- Guest workshop payment tracking

### 📦 Package System
- Create custom training packages (multi-month)
- Package enrollment with flexible payment options
- Payment deadline tracking
- Automatic monthly fee adjustment during package period

### 🎪 Workshop Management
- Workshop creation and management
- Student and guest enrollment
- Workshop fee tracking
- Optional monthly fee waiver for enrolled students
- Delete workshops with enrollment protection

### 🛍️ Inventory & Product Sales
- Product/clothing inventory management
- Stock tracking
- Student-wise sales records
- Sales history and reporting

### 💸 Expense Management
- Track academy expenses by category (Rent, Utility, Salary, Misc)
- Instructor salary tracking
- Expense voiding capability
- Date-wise expense reports

### 📊 Reports & Analytics
- **Income Reports**: Unified view of ledger transactions and guest payments
- **Defaulter Reports**: Track students with outstanding balances
- Date range filtering
- CSV export functionality
- Dashboard with key metrics

### 🔐 User Management & Security
- Role-based access control (Admin/Staff)
- **Granular Permissions System**:
  - Students & Profiles
  - Classes & Instructors
  - Attendance Tracking
  - Finance (Ledger)
  - Expenses Management
  - Analytics & Reports
  - System Settings
  - Workshops
  - Packages
  - Inventory/Products
- Secure password hashing
- Session management
- Admin-only sensitive operations

### 🌐 Nepali Date Support
- Full Bikram Sambat (BS) calendar integration
- Nepali date picker for all date inputs
- Automatic date conversion and formatting

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript
- **Date Handling**: nepali-datetime
- **UI/UX**: Custom glassmorphism design with dark theme

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Git (for version control)

## 🚀 Installation

1. **Clone the repository**
```bash
git clone https://github.com/besal25/dance-academy.git
cd dance-academy
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run database migrations**
```bash
python migrate.py
python migrate_permissions.py
```

4. **Start the application**
```bash
python app.py
```

5. **Access the application**
- Open your browser and go to: `http://127.0.0.1:5000`
- Default admin credentials:
  - Username: `admin`
  - Password: `admin123`

## 📁 Project Structure

```
dance-academy/
├── app.py                      # Main application entry point
├── database.py                 # Database models and schema
├── requirements.txt            # Python dependencies
├── routes/                     # Application routes
│   ├── auth.py                # Authentication & user management
│   ├── students.py            # Student management
│   ├── classes.py             # Class management
│   ├── attendance.py          # Attendance tracking
│   ├── finance.py             # Financial operations
│   ├── packages.py            # Package management
│   ├── workshops.py           # Workshop management
│   ├── inventory.py           # Inventory & sales
│   ├── expenses.py            # Expense tracking
│   ├── reports.py             # Reports & analytics
│   └── settings.py            # System settings
├── templates/                  # HTML templates
├── static/                     # CSS, JS, and uploads
├── instance/                   # Database files (auto-created)
└── tests/                      # Test suite
```

## 🔧 Configuration

### Default Settings
- **Admission Fee**: Rs 1000.0 (configurable in Settings)
- **Default Monthly Fee**: Rs 5000.0 (customizable per student)
- **Currency**: Nepali Rupees (NPR)

### Customization
- Modify `database.py` to adjust database schema
- Update `static/style.css` for UI customization
- Configure settings through the admin panel

## 📸 Key Features Highlights

### Package Protection Billing
- Automatically prevents double billing when students enroll in packages
- Voids overlapping monthly fees during package enrollment
- Smart fee generation skips students with active packages

### Workshop Fee Waiver
- Optional checkbox during workshop enrollment
- Automatically voids monthly fee when enabled
- Provides flexibility in billing for workshop participants

### Granular Permissions
- 10 different permission levels for fine-grained access control
- Toggle permissions per user with visual badge system
- Admin users have full access to all features

### Advanced Ledger System
- Tracks all financial transactions (Fees, Payments, Voids)
- Supports advance payments and credit balances
- Automatic balance calculation and recalculation
- Transaction voiding with balance adjustment

## 🧪 Testing

Run the verification script to test all features:
```bash
python verify_new_features.py
```

Run the full test suite:
```bash
python tests/run_tests.py
```

## 🔒 Security Features

- Password hashing with Werkzeug security
- Session-based authentication
- CSRF protection
- Role-based access control
- Admin-only sensitive operations
- Secure file upload handling

## 📝 License

This project is open source and available for educational and commercial use.

## 👨‍💻 Developer

**Bishal Khatiwada**
- GitHub: [@besal25](https://github.com/besal25)
- Email: bkhatiwada383@gmail.com

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📞 Support

For support, email bkhatiwada383@gmail.com or open an issue on GitHub.

---

**Built with ❤️ for dance academies worldwide**
