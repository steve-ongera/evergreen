# 🌾 Evergreen E-commerce

A modern Django-based e-commerce platform specifically designed for agricultural products, farming supplies, and rural commerce. Built with farmers and agricultural businesses in mind, featuring WhatsApp integration for seamless order management.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/django-4.0+-green.svg)

## 🚀 Features

### Core E-commerce Functionality
- **Product Catalog**: Comprehensive product management with categories, subcategories, and brands
- **Shopping Cart**: Session-based cart system with real-time updates
- **Search & Filter**: Advanced product search with filtering by category, price, and attributes
- **Product Reviews**: Customer review and rating system
- **Responsive Design**: Mobile-first design optimized for all devices

### Agricultural-Specific Features
- **Farm Information**: Customer profiles with farm details and farming type
- **Crop Categories**: Specialized categorization for crops, livestock, fertilizers, and equipment
- **Harvest & Expiry Tracking**: Date tracking for perishable agricultural products
- **Units Management**: Support for agricultural units (kg, liters, acres, etc.)
- **Organic Certification**: Organic product labeling and filtering

### WhatsApp Integration
- **WhatsApp Ordering**: Direct order placement through WhatsApp
- **Message Templates**: Pre-formatted order messages with customer and product details
- **Contact Methods**: Multiple contact options (WhatsApp, Phone, SMS)
- **Order Tracking**: WhatsApp-based order status updates

### Business Features
- **Inventory Management**: Real-time stock tracking with low-stock alerts
- **Order Management**: Comprehensive order processing workflow
- **Customer Management**: Detailed customer profiles and order history
- **Analytics Ready**: Built-in order tracking for business intelligence
- **Multi-Payment Support**: M-Pesa, Cash on Delivery, Bank Transfer, Card payments

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- PostgreSQL/MySQL (recommended) or SQLite (development)
- Git

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/evergreen-ecommerce.git
cd evergreen-ecommerce
```

### 2. Create Virtual Environment
```bash
python -m venv evergreen_env

# On Windows
evergreen_env\Scripts\activate

# On macOS/Linux
source evergreen_env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3

# WhatsApp Configuration
WHATSAPP_BUSINESS_NUMBER=254XXXXXXXXX

# Email Configuration (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Media and Static Files
MEDIA_URL=/media/
STATIC_URL=/static/
```

### 5. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Create Required Directories
```bash
mkdir logs
mkdir media
mkdir static
```

### 7. Load Sample Data (Optional)
```bash
python manage.py loaddata fixtures/sample_data.json
```

### 8. Run Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to view the application.

## 📁 Project Structure

```
evergreen-ecommerce/
├── evergreen/
│   ├── settings.py          # Django settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py             # WSGI configuration
├── apps/
│   ├── products/           # Product management
│   ├── orders/             # Order processing
│   ├── customers/          # Customer management
│   └── cart/               # Shopping cart
├── templates/
│   ├── base.html           # Base template
│   ├── checkout.html       # Checkout page
│   └── whatsapp_order.html # WhatsApp order confirmation
├── static/
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── img/               # Images
├── media/                 # User uploaded files
├── logs/                  # Application logs
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🔧 Configuration

### WhatsApp Integration
1. Update your WhatsApp business number in `settings.py`:
```python
WHATSAPP_BUSINESS_NUMBER = "254XXXXXXXXX"  # Your number with country code
```

2. Customize WhatsApp message templates in the views or create template files.

### Payment Integration
The system supports multiple payment methods:
- **M-Pesa**: Integrate with Safaricom M-Pesa API
- **Card Payments**: Integrate with payment processors like Stripe or Flutterwave
- **Bank Transfer**: Configure bank details in admin
- **Cash on Delivery**: Built-in support

### Email Configuration
Configure email settings for order confirmations and notifications:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-host'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

## 📱 Usage

### For Customers
1. **Browse Products**: Navigate through categories or use search
2. **Add to Cart**: Select products and quantities
3. **Checkout**: Fill in delivery details and contact information
4. **WhatsApp Order**: Send order directly via WhatsApp
5. **Order Confirmation**: Receive confirmation and delivery details

### For Administrators
1. **Admin Panel**: Access at `/admin/` with superuser credentials
2. **Product Management**: Add, edit, and manage products
3. **Order Processing**: View and process incoming orders
4. **Customer Management**: Manage customer profiles and history
5. **Inventory Tracking**: Monitor stock levels and low-stock alerts

## 🎨 Customization

### Styling
- Modify CSS files in `static/css/`
- Update templates in `templates/`
- Customize Bootstrap components as needed

### Adding New Features
1. Create new Django apps in the `apps/` directory
2. Update `INSTALLED_APPS` in settings
3. Create models, views, and templates
4. Update URL configurations

### WhatsApp Message Templates
Customize message formats in `views.py`:
```python
def generate_whatsapp_message(request):
    # Customize message template here
    message_parts = [
        "🌾 *NEW ORDER REQUEST* 🌾",
        # Add your custom message format
    ]
```

## 🧪 Testing

Run tests with:
```bash
python manage.py test
```

For specific app testing:
```bash
python manage.py test apps.products
python manage.py test apps.orders
```

## 🚀 Deployment

### Production Setup
1. **Update Settings**: Set `DEBUG=False` and configure allowed hosts
2. **Database**: Use PostgreSQL or MySQL for production
3. **Static Files**: Configure static file serving (WhiteNoise or CDN)
4. **Security**: Implement SSL/TLS certificates
5. **Environment Variables**: Use environment variables for sensitive data

### Deployment Platforms
- **Heroku**: Include `Procfile` and `runtime.txt`
- **DigitalOcean**: Use App Platform or Droplets
- **AWS**: Deploy on Elastic Beanstalk or EC2
- **Railway**: Simple deployment with Git integration

### Example Heroku Deployment
```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

## 📖 API Documentation

### REST API Endpoints (If implemented)
- `GET /api/products/` - List all products
- `GET /api/products/{id}/` - Get product details
- `POST /api/orders/` - Create new order
- `GET /api/categories/` - List categories

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Write tests for new features
- Update documentation for changes
- Use meaningful commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check this README and inline documentation
- **Issues**: Report bugs on GitHub Issues
- **Community**: Join our discussion forum
- **Email**: Contact support@evergreen-ecommerce.com

### Common Issues
1. **Migration Errors**: Delete migrations and recreate them
2. **Static Files**: Run `python manage.py collectstatic`
3. **Permission Errors**: Check file permissions on media directory
4. **WhatsApp Not Working**: Verify phone number format and URL encoding

## 🛣️ Roadmap

### Upcoming Features
- [ ] Mobile app (React Native/Flutter)
- [ ] Advanced analytics dashboard
- [ ] Multi-vendor marketplace
- [ ] Subscription-based products
- [ ] AI-powered product recommendations
- [ ] IoT integration for farm monitoring
- [ ] Multilingual support
- [ ] Advanced reporting system

### Version History
- **v1.0.0** - Initial release with core e-commerce features
- **v1.1.0** - WhatsApp integration
- **v1.2.0** - Enhanced agricultural features
- **v2.0.0** - Mobile app and API (Planned)

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Django community for the excellent framework
- Bootstrap team for responsive design components
- Font Awesome for icons
- Agricultural community for feature inspiration
- Open source contributors

## 📊 Statistics

- **Lines of Code**: ~5,000+
- **Models**: 15+
- **Views**: 25+
- **Templates**: 20+
- **Supported Languages**: English (Swahili support planned)
- **Target Market**: Kenya, East Africa

---

**Made By Steve Ongera  for farmers and agricultural communities**

For more information, visit our [documentation](https://evergreen-ecommerce.readthedocs.io) or [website](https://evergreen-ecommerce.com).