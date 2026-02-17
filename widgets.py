"""
Custom widgets for the Delivery Tracker application.
Includes dashboard, statistics, and enhanced UI components.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QPushButton, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPen
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from typing import Dict, Any, List
import utils


class StatCard(QFrame):
    """A card widget displaying a statistic"""
    
    def __init__(self, title: str, value: str, icon: str = "", color: str = "#2196F3", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            StatCard {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
                padding: 15px;
            }}
            StatCard:hover {{
                border: 2px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #757575; font-size: 12px; font-weight: normal;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold;")
        layout.addWidget(value_label)
        
        self.value_label = value_label
    
    def update_value(self, value: str):
        """Update the displayed value"""
        self.value_label.setText(value)


class DashboardWidget(QWidget):
    """Dashboard showing statistics and overview"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dashboard UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("📊 Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #212121;")
        main_layout.addWidget(title)
        
        # Stats Cards Container
        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)
        
        # Create stat cards
        self.total_card = StatCard("Totale Ordini", "0", color="#2196F3")
        self.pending_card = StatCard("In Attesa", "0", color="#FF9800")
        self.delivered_card = StatCard("Consegnati", "0", color="#4CAF50")
        self.overdue_card = StatCard("Scaduti", "0", color="#F44336")
        
        cards_layout.addWidget(self.total_card, 0, 0)
        cards_layout.addWidget(self.pending_card, 0, 1)
        cards_layout.addWidget(self.delivered_card, 0, 2)
        cards_layout.addWidget(self.overdue_card, 0, 3)
        
        main_layout.addLayout(cards_layout)
        
        # Charts Container
        charts_layout = QHBoxLayout()
        
        # Platform Distribution Chart
        self.platform_chart_view = self.create_pie_chart("Distribuzione per Piattaforma")
        charts_layout.addWidget(self.platform_chart_view)
        
        # Status Chart
        self.status_chart_view = self.create_bar_chart("Stato Consegne")
        charts_layout.addWidget(self.status_chart_view)
        
        main_layout.addLayout(charts_layout)
        
        main_layout.addStretch()
    
    def create_pie_chart(self, title: str) -> QChartView:
        """Create a pie chart widget"""
        series = QPieSeries()
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(300)
        
        return chart_view
    
    def create_bar_chart(self, title: str) -> QChartView:
        """Create a bar chart widget"""
        series = QBarSeries()
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(300)
        
        return chart_view
    
    def update_stats(self, orders: List[Dict[str, Any]]):
        """Update dashboard with new data"""
        if not orders:
            return
        
        # Calculate statistics
        stats = utils.StatisticsCalculator.calculate_stats(orders)
        
        # Update stat cards
        self.total_card.update_value(str(stats['total']))
        self.pending_card.update_value(str(stats['pending']))
        self.delivered_card.update_value(str(stats['delivered']))
        self.overdue_card.update_value(str(stats['overdue']))
        
        # Update platform chart
        self.update_platform_chart(stats['platforms'])
        
        # Update status chart
        self.update_status_chart(stats)
    
    def update_platform_chart(self, platforms: Dict[str, int]):
        """Update the platform distribution pie chart"""
        chart = self.platform_chart_view.chart()
        chart.removeAllSeries()
        
        series = QPieSeries()
        
        # Sort platforms by count
        sorted_platforms = sorted(platforms.items(), key=lambda x: x[1], reverse=True)
        
        # Show top 5 platforms, group others
        top_platforms = sorted_platforms[:5]
        others_count = sum(count for _, count in sorted_platforms[5:])
        
        for platform, count in top_platforms:
            slice = series.append(f"{platform} ({count})", count)
            slice.setLabelVisible(True)
        
        if others_count > 0:
            slice = series.append(f"Altri ({others_count})", others_count)
            slice.setLabelVisible(True)
        
        chart.addSeries(series)
    
    def update_status_chart(self, stats: Dict[str, Any]):
        """Update the status bar chart"""
        chart = self.status_chart_view.chart()
        chart.removeAllSeries()
        
        # Create bar set
        bar_set = QBarSet("Ordini")
        bar_set.append(stats['overdue'])
        bar_set.append(stats['due_today'])
        bar_set.append(stats['upcoming'])
        bar_set.append(stats['delivered'])
        
        # Create series
        series = QBarSeries()
        series.append(bar_set)
        
        # Add series to chart
        chart.addSeries(series)
        
        # Setup axes
        categories = ["Scaduti", "Oggi", "In Arrivo", "Consegnati"]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, max(stats['overdue'], stats['due_today'], stats['upcoming'], stats['delivered']) + 5)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)


class SearchFilterBar(QWidget):
    """Search and filter bar widget"""
    
    search_changed = pyqtSignal(str)
    filter_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the search/filter UI"""
        from PyQt6.QtWidgets import QLineEdit, QComboBox, QCheckBox
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Cerca ordini...")
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setMinimumWidth(250)
        layout.addWidget(self.search_input)
        
        # Platform filter
        platform_label = QLabel("Piattaforma:")
        layout.addWidget(platform_label)
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItem("Tutte", "")
        self.platform_combo.currentIndexChanged.connect(self.on_filter_changed)
        layout.addWidget(self.platform_combo)
        
        # Category filter
        category_label = QLabel("Categoria:")
        layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("Tutte", "")
        self.category_combo.currentIndexChanged.connect(self.on_filter_changed)
        layout.addWidget(self.category_combo)
        
        # Show delivered checkbox
        self.show_delivered_cb = QCheckBox("Consegnati")
        self.show_delivered_cb.setChecked(True)
        self.show_delivered_cb.stateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.show_delivered_cb)
        
        layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Pulisci Filtri")
        clear_btn.clicked.connect(self.clear_filters)
        layout.addWidget(clear_btn)
    
    def on_search_changed(self):
        """Emit search changed signal"""
        self.search_changed.emit(self.search_input.text())
    
    def on_filter_changed(self):
        """Emit filter changed signal"""
        filters = {
            'platform': self.platform_combo.currentData(),
            'category': self.category_combo.currentData(),
            'show_delivered': self.show_delivered_cb.isChecked()
        }
        self.filter_changed.emit(filters)
    
    def clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.platform_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        self.show_delivered_cb.setChecked(True)
    
    def update_platforms(self, platforms: List[str]):
        """Update platform filter options"""
        current = self.platform_combo.currentData()
        self.platform_combo.clear()
        self.platform_combo.addItem("Tutte", "")
        
        for platform in platforms:
            self.platform_combo.addItem(platform, platform)
        
        # Restore selection if possible
        index = self.platform_combo.findData(current)
        if index >= 0:
            self.platform_combo.setCurrentIndex(index)
    
    def update_categories(self, categories: List[str]):
        """Update category filter options"""
        current = self.category_combo.currentData()
        self.category_combo.clear()
        self.category_combo.addItem("Tutte", "")
        
        for category in categories:
            self.category_combo.addItem(category, category)
        
        # Restore selection if possible
        index = self.category_combo.findData(current)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
