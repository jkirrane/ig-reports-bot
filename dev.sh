#!/bin/bash
# Quick commands for IG Reports Bot development

echo "🛡️ IG Reports Bot - Quick Commands"
echo "=================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Run: source venv/bin/activate"
    echo ""
fi

# Function to show help
show_help() {
    echo "Available commands:"
    echo ""
    echo "Setup & Configuration:"
    echo "  ./dev.sh setup          - Install dependencies"
    echo "  ./dev.sh test-setup     - Validate installation"
    echo "  ./dev.sh init-db        - Initialize database"
    echo ""
    echo "Testing Components:"
    echo "  ./dev.sh test-scraper   - Test Oversight.gov scraper"
    echo "  ./dev.sh test-filter    - Test LLM filter"
    echo "  ./dev.sh test-summary   - Test summary generator"
    echo ""
    echo "Running Pipeline:"
    echo "  ./dev.sh dry-run        - Dry run (no saves, no costs)"
    echo "  ./dev.sh run            - Full pipeline"
    echo "  ./dev.sh scrape-only    - Only scraping phase"
    echo ""
    echo "Database:"
    echo "  ./dev.sh db-stats       - Show database statistics"
    echo "  ./dev.sh db-shell       - Open SQLite shell"
    echo "  ./dev.sh db-reset       - Reset database (caution!)"
    echo ""
    echo "Monitoring:"
    echo "  ./dev.sh costs          - Show LLM costs"
    echo "  ./dev.sh logs           - View pipeline logs"
    echo "  ./dev.sh decisions      - Review LLM decisions"
    echo ""
}

# Parse command
case "$1" in
    setup)
        echo "📦 Installing dependencies..."
        pip install -r requirements.txt
        echo "✅ Done! Run './dev.sh test-setup' to validate"
        ;;
    
    test-setup)
        echo "🧪 Running setup validation..."
        python test_setup.py
        ;;
    
    init-db)
        echo "🗄️ Initializing database..."
        python -m database.db
        ;;
    
    test-scraper)
        echo "🕷️ Testing scraper..."
        python -m scrapers.oversight_gov
        ;;
    
    test-filter)
        echo "🤖 Testing LLM filter..."
        python -m llm.filter
        ;;
    
    test-summary)
        echo "✍️ Testing summary generator..."
        python -m llm.summary
        ;;
    
    dry-run)
        echo "🔄 Running pipeline in dry-run mode..."
        python run_daily.py --dry-run --days-back 2
        ;;
    
    run)
        echo "🚀 Running full pipeline..."
        python run_daily.py
        ;;
    
    scrape-only)
        echo "🕷️ Running scraper only..."
        python run_daily.py --skip-filtering --skip-summary
        ;;
    
    db-stats)
        echo "📊 Database statistics..."
        python -m database.db
        ;;
    
    db-shell)
        echo "🐚 Opening SQLite shell..."
        echo "Useful queries:"
        echo "  SELECT COUNT(*) FROM ig_reports;"
        echo "  SELECT * FROM ig_reports WHERE passed_llm_filter = 1 LIMIT 5;"
        echo "  .schema"
        echo ""
        sqlite3 database/ig_reports.db
        ;;
    
    db-reset)
        echo "⚠️  WARNING: This will delete all data!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            rm -f database/ig_reports.db
            python -m database.db
            echo "✅ Database reset"
        else
            echo "❌ Cancelled"
        fi
        ;;
    
    costs)
        echo "💰 LLM usage costs..."
        if [ -f llm_usage.log ]; then
            python -c "from llm import get_total_cost; print(f'Total cost: \${get_total_cost():.4f}')"
            echo ""
            echo "Last 5 API calls:"
            tail -5 llm_usage.log | python -c "import sys, json; [print(f'{json.loads(line)[\"timestamp\"]}: \${json.loads(line)[\"cost\"]:.4f} ({json.loads(line)[\"total_tokens\"]} tokens)') for line in sys.stdin]"
        else
            echo "No usage log found yet"
        fi
        ;;
    
    logs)
        echo "📋 Recent pipeline logs..."
        if [ -f pipeline.log ]; then
            tail -50 pipeline.log
        else
            echo "No logs found yet"
        fi
        ;;
    
    decisions)
        echo "🤔 Recent LLM filter decisions..."
        if [ -f llm_decisions.log ]; then
            echo "Last 5 decisions:"
            tail -5 llm_decisions.log | python -c "import sys, json; [print(f'\n{json.loads(line)[\"title\"]}\n  Score: {json.loads(line)[\"decision\"][\"score\"]}/10\n  Newsworthy: {json.loads(line)[\"decision\"][\"newsworthy\"]}\n  Reason: {json.loads(line)[\"decision\"][\"reason\"]}') for line in sys.stdin]"
        else
            echo "No decisions log found yet"
        fi
        ;;
    
    help|--help|-h|"")
        show_help
        ;;
    
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
