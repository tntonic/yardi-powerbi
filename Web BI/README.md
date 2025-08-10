# Yardi PowerBI Web Dashboard

## 🏢 Interactive Commercial Real Estate Analytics Platform

A modern, responsive web-based dashboard for commercial real estate analytics built with Streamlit and DuckDB. This platform provides comprehensive insights into portfolio performance, leasing activity, financial metrics, and credit risk analysis.

## ✨ Key Features

### 📊 Dashboard Components
- **Executive Summary**: High-level portfolio KPIs and performance indicators
- **Rent Roll Analysis**: Detailed rent roll analysis and tenant information
- **Leasing Activity**: Leasing performance and market analysis
- **Financial Performance**: Comprehensive financial metrics and reporting
- **Credit Risk Analysis**: Tenant credit scoring and risk assessment

### 🚀 Enhanced User Experience
- **Modern UI/UX**: Beautiful, responsive design with gradient styling
- **Real-time Analytics**: Live data updates and interactive visualizations
- **Advanced Filtering**: Property search, date range selection, and fund filtering
- **Export Capabilities**: Download data in CSV format with timestamps
- **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices

### 🛡️ Robust Error Handling
- **User-Friendly Errors**: Clear, actionable error messages
- **Performance Monitoring**: Automatic detection of slow operations
- **Data Validation**: Comprehensive input validation and data quality checks
- **Graceful Degradation**: Continued operation even with partial data issues

### ⚡ Performance Optimizations
- **Smart Caching**: 5-10 minute cache for expensive queries
- **Query Optimization**: Optimized database queries for better performance
- **Lazy Loading**: Load components only when needed
- **Memory Management**: Efficient handling of large datasets

## 🛠️ Technical Stack

- **Frontend**: Streamlit 1.40.2
- **Database**: DuckDB 1.1.3
- **Data Processing**: Pandas 2.2.3, NumPy 1.26.4
- **Visualization**: Plotly 5.24.1
- **Configuration**: PyYAML 6.0.2
- **Utilities**: Python-dateutil 2.9.0

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Access to Yardi database files

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Yardi PowerBI/Web BI"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   cd database
   python init_db.py
   cd ..
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the dashboard**
   Open your browser and navigate to `http://localhost:8501`

## 🎯 Quick Start

1. **Select Dashboard**: Choose from the available dashboard views in the sidebar
2. **Set Filters**: Configure date range, properties, funds, and books
3. **Explore Data**: Interact with charts, tables, and metrics
4. **Export Results**: Download data for further analysis

## 📊 Dashboard Features

### Executive Summary
- Portfolio-level KPIs and performance metrics
- Revenue and NOI analysis by property
- Portfolio summary with export capabilities
- Key insights and performance indicators

### Rent Roll Analysis
- Detailed rent roll data and tenant information
- Occupancy and rent collection metrics
- Property performance comparisons
- Historical trend analysis

### Leasing Activity
- Leasing velocity and market performance
- New lease and renewal analysis
- Market absorption and vacancy trends
- Tenant movement tracking

### Financial Performance
- Comprehensive financial reporting
- NOI and cash flow analysis
- Budget vs. actual comparisons
- Fund and book-specific metrics

### Credit Risk Analysis
- Tenant credit scoring and risk assessment
- Portfolio risk distribution
- Credit coverage analysis
- Risk mitigation recommendations

## ⚙️ Configuration

The dashboard is highly configurable through the `config/settings.yaml` file:

```yaml
# Dashboard Settings
dashboard:
  title: "Yardi PowerBI Dashboard"
  version: "5.1"
  theme: "light"

# Performance Settings
performance:
  cache_ttl: 300  # 5 minutes
  slow_query_threshold: 2.0

# UI Settings
ui:
  page_layout: "wide"
  chart_height: 400
```

## 🔧 Customization

### Adding New Components
1. Create a new component file in `components/`
2. Implement the render function following the existing pattern
3. Add the component to the main app navigation
4. Update configuration as needed

### Customizing Styling
- Modify CSS in `app.py` for global styling
- Use the configuration file for theme settings
- Customize chart colors and layouts

### Extending Functionality
- Add new utility functions in `utils/`
- Implement new error handling patterns
- Extend the configuration system

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
- Ensure the database file exists in `database/yardi.duckdb`
- Check file permissions
- Run the database initialization script

**Slow Performance**
- Check the cache settings in configuration
- Limit the number of selected properties
- Reduce the date range for analysis

**Missing Data**
- Verify data availability in the database
- Check filter settings
- Ensure proper data format

### Getting Help
- Check the `IMPROVEMENTS.md` file for detailed information
- Review error messages for specific guidance
- Contact support for persistent issues

## 📈 Performance Tips

1. **Use Appropriate Filters**: Limit date ranges and property selections
2. **Enable Caching**: Keep caching enabled for better performance
3. **Monitor Queries**: Watch for slow query warnings
4. **Export Large Datasets**: Use export functionality for large data analysis

## 🔒 Security

- **Read-Only Database**: Database is accessed in read-only mode
- **Input Validation**: All user inputs are validated
- **Error Information**: Limited error information exposure
- **Session Management**: Secure session handling

## 📝 Documentation

- **IMPROVEMENTS.md**: Comprehensive improvement documentation
- **Configuration Guide**: Settings and customization options
- **Component Documentation**: Individual component guides
- **API Reference**: Utility and helper function documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Email: support@example.com
- Documentation: [GitHub Wiki](https://github.com/your-username/yardi-powerbi/wiki)
- Issues: [GitHub Issues](https://github.com/your-username/yardi-powerbi/issues)

---

**Version**: 5.1  
**Last Updated**: December 2024  
**Maintained by**: Yardi PowerBI Development Team