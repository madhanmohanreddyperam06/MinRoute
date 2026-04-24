# 🚚 Delivery Route Optimization System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29.0-FF4B4B)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Algorithm](https://img.shields.io/badge/Algorithm-Dijkstra's%20Shortest%20Path-orange)](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)

A comprehensive logistics route planner that uses **Dijkstra's Shortest Path Algorithm** to determine the most efficient delivery routes from a warehouse to multiple delivery locations.

## 🌟 Features

- **Smart Geocoding**: Convert addresses to coordinates using geopy and Nominatim API
- **⚡ Real-time Geocoding**: Automatic coordinate analysis when locations are added
- **📏 Distance Calculation**: Accurate distance calculation using Haversine formula
- **🗺️ Interactive Maps**: Beautiful route visualization with Folium
- **🎯 Route Optimization**: Dijkstra's algorithm for shortest path finding
- **📊 Analytics Dashboard**: Comprehensive delivery metrics and insights
- **🎨 Modern UI**: Clean and intuitive Streamlit interface with live feedback

## 🏗️ Project Structure

```text
Delivery Route Optimization System/
├── app.py                    # Main Streamlit application
├── geocoding.py              # Address to coordinate conversion
├── distance_calculator.py    # Haversine distance calculations
├── graph_builder.py          # Graph construction for locations
├── dijkstra_algorithm.py     # Dijkstra's shortest path implementation
├── map_visualizer.py         # Interactive map creation
├── analytics.py              # Delivery analytics and metrics
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download the project files**
2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:

   ```bash
   streamlit run app.py
   ```

4. **Open your browser** and navigate to `http://localhost:8501`

## 📋 Usage Guide

### 1. Set Warehouse Location

- Enter warehouse address (e.g., "Chennai Central")
- **Automatic Geocoding**: Coordinates are analyzed instantly as you type
- View precise latitude/longitude coordinates in real-time
- Green confirmation box appears when geocoding succeeds

### 2. Add Delivery Locations

- **Dynamic Input**: Enter delivery addresses one by one
- **➕ Add Button**: Click to automatically geocode and add each location
- **🗑️ Clear All**: Remove all delivery locations at once
- **Individual Management**: Edit (✏️) or remove (🗑️) specific locations

### 3. Monitor Location Status

- **Real-time Feedback**: See coordinates immediately for each location
- **Status Indicators**: ✅ Ready / ⚠️ Pending for each delivery point
- **Progress Summary**: "3/4 locations geocoded and ready for optimization"
- **Visual Layout**: Structured cards with color-coded status

### 4. Optimize Route

- Click "🚀 Optimize Route" once all locations are ready
- **Instant Processing**: Uses pre-geocoded coordinates for faster optimization
- **Dijkstra's Algorithm**: Finds shortest paths automatically
- **Comprehensive Results**: Route order, map, and analytics

### 5. View Results

- **Optimized Route**: Numbered delivery sequence from warehouse
- **Interactive Map**: Visual route with distance labels
- **Analytics Dashboard**: Fuel, time, and efficiency metrics

## 🧠 Algorithm Details

### Dijkstra's Shortest Path Algorithm

The application uses Dijkstra's algorithm because:

- **Guaranteed Optimality**: Always finds the shortest path in weighted graphs
- **Perfect for Logistics**: Delivery locations form a weighted graph with distances as edge weights
- **Efficient Performance**: O((V + E) log V) time complexity with priority queue

### Distance Calculation

Uses the **Haversine formula** to calculate great-circle distances between coordinates:

```text
a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
c = 2 ⋅ atan2( √a, √(1−a) )
d = R ⋅ c
```

Where R = Earth's radius (6371 km)

## 📊 Analytics Features

### Route Metrics

- **Total Distance**: Complete route length in kilometers
- **Number of Stops**: Total delivery locations
- **Fuel Consumption**: Estimated fuel usage and cost
- **Delivery Time**: Travel time + stop time

### Efficiency Analysis

- **Distance per Delivery**: Average distance per stop
- **Route Savings**: Optimization benefits
- **Efficiency Score**: Overall route performance rating

## 🎨 UI Features

### Modern Design

- **Responsive Layout**: Works on all screen sizes
- **Visual Indicators**: Color-coded markers and routes
- **Interactive Elements**: Real-time updates and feedback
- **Professional Styling**: Clean, logistics-themed interface

### Map Visualization

- **Warehouse Marker**: Green icon for starting point
- **Delivery Markers**: Blue icons for destinations
- **Route Lines**: Red polylines showing optimized path
- **Distance Labels**: Kilometer markers on route

## 🔧 Technical Implementation

### Core Modules

1. **Geocoding Module** (`geocoding.py`)
   - Address validation and conversion
   - Error handling for invalid addresses
   - Batch processing for multiple locations

2. **Distance Calculator** (`distance_calculator.py`)
   - Haversine formula implementation
   - Distance matrix generation
   - Route distance calculations

3. **Graph Builder** (`graph_builder.py`)
   - Graph data structure
   - Complete graph construction
   - Node and edge management

4. **Dijkstra Algorithm** (`dijkstra_algorithm.py`)
   - Priority queue implementation
   - Shortest path calculation
   - Route optimization logic

5. **Map Visualizer** (`map_visualizer.py`)
   - Folium map creation
   - Custom markers and styling
   - Interactive features

6. **Analytics** (`analytics.py`)
   - Performance metrics
   - Cost calculations
   - Efficiency scoring

## 🌍 Example Usage

### Sample Input

- **Warehouse**: Chennai Central
- **Deliveries**: T Nagar, Adyar, Velachery, Anna Nagar

### Sample Output

- **Optimized Route**: Chennai Central → T Nagar → Adyar → Velachery → Anna Nagar
- **Total Distance**: 28.5 km
- **Estimated Time**: 42 minutes
- **Fuel Required**: 1.9 liters

## 🛠️ Dependencies

```text
streamlit==1.29.0      # Web application framework
folium==0.15.0         # Interactive maps
streamlit-folium==0.19.0 # Streamlit-Folium integration
geopy==2.4.1           # Geocoding services
numpy==1.24.3          # Numerical computations
```

## 🎯 Hackathon Tips

### Why Dijkstra's Algorithm?
>
> "Dijkstra's Algorithm guarantees the shortest path in weighted graphs. Since delivery locations form a weighted graph with distances as edge weights, it ensures optimal routing for logistics systems."

### Demo Suggestions

1. **Start with a simple example**: 3-4 locations in the same city
2. **Show the optimization process**: Display distance matrix and graph
3. **Highlight the benefits**: Compare optimized vs. unoptimized routes
4. **Demonstrate scalability**: Add more locations to show efficiency

## 🐛 Troubleshooting

### Common Issues

1. **Geocoding Errors**
   - Check internet connection
   - Verify address spelling
   - Try more specific addresses

2. **Map Not Loading**
   - Ensure all dependencies are installed
   - Check browser console for errors
   - Refresh the application

3. **Slow Performance**
   - Limit to 10-15 locations for optimal performance
   - Check system resources

### Error Messages

- `⚠️ Address not found`: Try a more specific address
- `❌ Could not geocode`: Verify location names
- `⚠️ Please enter warehouse location`: Add warehouse first

## 🚀 Future Enhancements

### Advanced Features

- **Real-time Traffic Integration**: Use traffic APIs for dynamic routing
- **Vehicle Capacity Optimization**: Consider load constraints
- **Multiple Warehouse Support**: Route planning for multiple depots
- **Time Window Constraints**: Delivery scheduling
- **Cost Optimization**: Include fuel prices and tolls

### AI/ML Integration

- **Route Prediction**: Machine learning for pattern recognition
- **Demand Forecasting**: Predict delivery volumes
- **Dynamic Optimization**: Real-time route adjustments

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Verify all dependencies are installed
3. Ensure proper internet connectivity for geocoding

## 📧 Contact Information

### Madhan Mohan Reddy

- 📧 [Email](mailto:madhanmohanreddyperam06@gmail.com)
- 📱 **Mobile**: +91 9110395993

---

**🚚 Optimizing deliveries, one route at a time!**
