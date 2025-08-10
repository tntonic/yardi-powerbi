# Yardi PowerBI Web Dashboard

🏢 **Interactive commercial real estate analytics dashboard** built with Streamlit and DuckDB, providing real-time insights into your Yardi data with 95-99% accuracy against native reports.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- 61MB of CSV data in `../Data/Yardi_Tables/` directory
- Git (for deployment to GitHub)

### Installation

1. **Navigate to the Web BI directory**:
   ```bash
   cd "Yardi PowerBI/Web BI"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   cd database
   python init_db.py
   cd ..
   ```

4. **Run the dashboard**:
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** to `http://localhost:8501`

## 📊 Features

### 🎯 Executive Summary
- Portfolio KPIs (occupancy, NOI, health scores)
- Performance trends and property matrix
- Real-time insights and recommendations

### 🏠 Rent Roll Analysis  
- Amendment-based rent roll with 95-99% accuracy
- Credit risk integration and PSF analysis
- Tenant details with export capabilities

### 🏃 Leasing Activity
- New leases, renewals, terminations tracking
- Net absorption analysis and retention rates
- Activity trends by property and time

### 💰 Financial Performance
- Revenue, expense, and NOI analysis
- Financial ratios and PSF metrics
- Expense breakdown and property comparisons

### ⚠️ Credit Risk Analysis
- Tenant credit scoring (0-10 scale)
- Portfolio risk assessment by property/industry
- High-risk tenant identification

## 🏗️ Architecture

### Data Flow
```
CSV Files (32 tables) → DuckDB → SQL Views → Streamlit Dashboard
        61MB           In-memory    DAX Logic    Interactive UI
```

### Core Components

- **DuckDB Database**: High-performance OLAP engine for complex queries
- **SQL Views**: Replicates Power BI DAX logic with 95-99% accuracy
- **Streamlit Frontend**: Interactive web interface with real-time filtering
- **Amendment Logic**: Critical rent roll calculations using latest sequences

### Key Tables
- `v_latest_amendments` - Latest amendment sequences (95-99% accuracy)
- `v_current_rent_roll` - Current rent roll with credit scores  
- `v_financial_ratios` - NOI, margins, PSF calculations
- `v_portfolio_health_score` - Composite performance metrics (0-100)

## 🚀 Deployment Options

### Option 1: Streamlit Community Cloud (Recommended)

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "🏢 Add Yardi PowerBI Web Dashboard"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set main file path: `Web BI/app.py`
   - Click "Deploy"

3. **Benefits**:
   - ✅ Free hosting for public repos
   - ✅ Automatic HTTPS and domain
   - ✅ Auto-redeploy on git push
   - ✅ Built-in authentication options

### Option 2: GitHub Pages + Static Export

1. **Generate static snapshots**:
   ```bash
   # Create static HTML exports (add this script)
   python utils/generate_static.py
   ```

2. **Deploy to GitHub Pages**:
   ```bash
   git checkout -b gh-pages
   git add static/
   git commit -m "🌐 Static dashboard export"
   git push origin gh-pages
   ```

3. **Enable GitHub Pages** in repository settings

### Option 3: Docker Deployment

1. **Build Docker image**:
   ```bash
   docker build -t yardi-dashboard .
   ```

2. **Run container**:
   ```bash
   docker run -p 8501:8501 yardi-dashboard
   ```

## 📁 Project Structure

```
Web BI/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── config/
│   └── settings.yaml        # Configuration settings
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── database/
│   ├── init_db.py          # Database initialization
│   ├── advanced_views.sql   # Complex SQL views
│   └── yardi.duckdb        # DuckDB database file
├── components/
│   ├── executive_summary.py # Executive dashboard
│   ├── rent_roll.py        # Rent roll analysis
│   ├── leasing_activity.py # Leasing metrics
│   ├── financial_metrics.py# Financial performance
│   └── credit_risk.py      # Credit risk analysis
├── utils/
│   └── data_loader.py      # Data loading utilities
└── static/                 # Static assets (generated)
```

## ⚙️ Configuration

### Database Settings (`config/settings.yaml`)
```yaml
database:
  path: "database/yardi.duckdb" 
  read_only: true
  timeout: 30

performance:
  max_query_timeout: 30
  chart_sample_size: 10000
  enable_caching: true
```

### UI Customization (`.streamlit/config.toml`)
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

## 🔧 Development

### Adding New Dashboards

1. **Create component file**:
   ```python
   # components/new_dashboard.py
   def render_new_dashboard(dashboard, filters...):
       st.header("New Dashboard")
       # Dashboard logic here
   ```

2. **Add to main app**:
   ```python
   # app.py
   from components.new_dashboard import render_new_dashboard
   
   if dashboard_choice == "New Dashboard":
       render_new_dashboard(dashboard, filters...)
   ```

### Custom SQL Views

1. **Add to `database/advanced_views.sql`**:
   ```sql
   CREATE OR REPLACE VIEW v_custom_metrics AS
   SELECT ... -- Custom logic here
   ```

2. **Update in `database/init_db.py`**:
   ```python
   self.conn.execute(open('advanced_views.sql').read())
   ```

## 📈 Performance

### Current Benchmarks
- **Database Load**: < 30 seconds (61MB CSV → DuckDB)
- **Dashboard Load**: < 5 seconds
- **Query Response**: < 2 seconds (typical)
- **Memory Usage**: ~200MB (including data)

### Optimization Tips
- Enable query caching (`enable_caching: true`)
- Limit chart sample sizes (`chart_sample_size: 10000`)
- Use materialized views for complex queries
- Implement pagination for large tables

## 🔒 Security

### Production Deployment
1. **Enable authentication**:
   ```yaml
   security:
     enable_auth: true
   ```

2. **Environment variables**:
   ```bash
   export STREAMLIT_AUTH_TOKEN="your-secure-token"
   ```

3. **Database encryption** (if needed):
   ```python
   conn = duckdb.connect("encrypted.duckdb", config={'password': 'secret'})
   ```

## 🧪 Testing

### Data Validation
```bash
# Run accuracy tests
cd ../Development/Python_Scripts
python top_20_measures_accuracy_test.py

# Validate amendment logic  
python amendment_logic_validator.py
```

### Dashboard Testing
```bash
# Run test suite (create test_dashboard.py)
pytest tests/
```

## 📊 Accuracy Validation

This dashboard replicates Power BI DAX calculations with proven accuracy:

- **Rent Roll**: 95-99% vs Yardi native reports
- **Financial Metrics**: 98%+ vs GL data  
- **Leasing Activity**: 95-98% vs source systems
- **Amendment Logic**: Validated against 122 production DAX measures

### Critical Implementation Notes
1. **Amendment filtering**: Always use latest sequence per property/tenant
2. **Revenue sign**: GL stores revenue as negative (multiply by -1)
3. **Status filtering**: Include both "Activated" AND "Superseded"
4. **Date handling**: Proper conversion of Excel serial dates

## 🆘 Troubleshooting

### Common Issues

**Database not found**:
```bash
cd database && python init_db.py
```

**Import errors**:
```bash
pip install -r requirements.txt
```

**Rent roll totals don't match**:
- Check amendment status filtering (Activated + Superseded)
- Verify latest sequence logic
- Review revenue sign convention

**Performance issues**:
- Enable caching in settings.yaml
- Reduce chart sample sizes
- Check database indexes

### Logs and Debugging
```bash
# Enable debug logging
export STREAMLIT_LOGGER_LEVEL=debug

# View dashboard logs
tail -f logs/dashboard.log
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is part of the Yardi PowerBI reference implementation. See main repository for license details.

## 🔗 Related Files

- **DAX Measures**: `../Documentation/Core_Guides/Complete_DAX_Library_v4_Production.dax`
- **Validation Scripts**: `../Development/Python_Scripts/`
- **Test Framework**: `../Development/Test_Automation_Framework/`
- **Clean Reference**: `../Claude_AI_Reference/`

---

**🏢 Built for commercial real estate professionals who demand accuracy and insights**