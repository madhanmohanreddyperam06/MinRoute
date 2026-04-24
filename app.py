"""
🚚 Delivery Route Optimization System
Main Streamlit Application - Dijkstra's Algorithm for Route Optimization
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple

# Import custom modules
from geocoding import Geocoder
from distance_calculator import DistanceCalculator
from graph_builder import GraphBuilder
from dijkstra_algorithm import DijkstraOptimizer
from map_visualizer import MapVisualizer
from analytics import DeliveryAnalytics


class DeliveryRouteApp:
    """Main application class for Delivery Route Optimization"""
    
    def __init__(self):
        """Initialize the application"""
        self.geocoder = Geocoder()
        self.distance_calculator = DistanceCalculator()
        self.map_visualizer = MapVisualizer()
        self.analytics = DeliveryAnalytics()
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'warehouse' not in st.session_state:
            st.session_state.warehouse = ""
        if 'delivery_locations' not in st.session_state:
            st.session_state.delivery_locations = []
        if 'location_input' not in st.session_state:
            st.session_state.location_input = ""
        if 'optimized_route' not in st.session_state:
            st.session_state.optimized_route = None
        if 'route_map' not in st.session_state:
            st.session_state.route_map = None
        # Add geocoded locations storage
        if 'geocoded_locations' not in st.session_state:
            st.session_state.geocoded_locations = {}
        if 'warehouse_coords' not in st.session_state:
            st.session_state.warehouse_coords = None
        # Add input counter for refreshing input fields
        if 'input_counter' not in st.session_state:
            st.session_state.input_counter = 0
    
    def run(self):
        """Run the main application"""
        self._setup_page_config()
        self._display_header()
        self._display_input_section()
        self._display_optimization_button()
        self._display_results()
    
    def _setup_page_config(self):
        """Setup Streamlit page configuration with enhanced styling"""
        st.set_page_config(
            page_title="Delivery Route Optimization System",
            page_icon="🚚",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Add global CSS for Times New Roman font
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Times+New+Roman:wght@300;400;600;700&display=swap');
        
        * {
            font-family: 'Times New Roman', serif !important;
        }
        
        body, .streamlit-container, .main, .block-container {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stApp, .stAppViewContainer {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stText, .stMarkdown, .stCaption {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stHeader, .stSubheader {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stButton > button {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stMetric > div > div > label,
        .stMetric > div > div > div {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stDataFrame, .stTable {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stInfo, .stSuccess, .stWarning, .stError {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stExpander {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stProgress > div > div > div {
            font-family: 'Times New Roman', serif !important;
        }
        
        .stAlert, .stException {
            font-family: 'Times New Roman', serif !important;
        }
        
        /* Force Times New Roman for all text elements */
        div, p, h1, h2, h3, h4, h5, h6, span, label, button, input, select, textarea, table, td, th {
            font-family: 'Times New Roman', serif !important;
        }
        
        /* Specific table text targeting */
        .dataframe, .stDataFrame table, .stDataFrame td, .stDataFrame th,
        .stTable table, .stTable td, .stTable th {
            font-family: 'Times New Roman', serif !important;
        }
        
        /* Table cell specific targeting */
        td[data-testid="stDataFrame"], th[data-testid="stDataFrame"],
        .stDataFrame [data-testid*="cell"], .stTable [data-testid*="cell"] {
            font-family: 'Times New Roman', serif !important;
        }
        
        /* Metric value targeting */
        [data-testid="metric-value"] {
            font-family: 'Times New Roman', serif !important;
        }
        
        /* Table content specific */
        .stDataFrame div[data-testid*="element-container"] {
            font-family: 'Times New Roman', serif !important;
        }

        /* Mobile-specific adjustments for coordinate input fields */
        @media (max-width: 768px) {
            /* Target coordinate display input fields in delivery locations */
            .stTextInput[data-testid*="stTextInput"]:has(input[readonly]),
            .stTextInput:has(input[value*=","]) {
                font-size: 0.75em !important;
                padding: 0.25em 0.5em !important;
                min-height: 2.5em !important;
            }
            
            /* Adjust column layout for mobile */
            .stColumns > div {
                padding: 0.25rem !important;
            }
            
            /* Coordinate input specific styling */
            input[readonly][value*=","] {
                font-size: 0.7em !important;
                padding: 0.2em 0.4em !important;
                line-height: 1.2 !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _display_header(self):
        """Display application header with enhanced beautiful styling"""
        # Enhanced header with red gradient background and smaller size
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #FF4B4B 0%, #E53E3E 100%);
            padding: 1.5rem 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            text-align: center;
            box-shadow: 0 8px 20px rgba(255, 75, 75, 0.3);
            position: relative;
            overflow: hidden;
            font-family: 'Times New Roman', serif;
        ">
            <div style="
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
                transform: rotate(45deg);
                animation: shine 3s infinite;
            "></div>
            <div style="position: relative; z-index: 1;">
                <h1 style="
                    color: white;
                    font-size: 2rem;
                    font-weight: 700;
                    margin: 0;
                    text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
                    letter-spacing: 1px;
                    animation: fadeInUp 1s ease-out;
                    font-family: 'Times New Roman', serif;
                ">
                    Delivery Route Optimizer
                </h1>
                <p style="
                    color: rgba(255,255,255,0.9);
                    font-size: 1.1rem;
                    margin: 0.5rem 0 0 0;
                    font-weight: 300;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                    animation: fadeInUp 1s ease-out 0.3s both;
                    font-family: 'Times New Roman', serif;
                ">
                    Smart routes for swift deliveries 🚚
                </p>
            </div>
        </div>
        
        <style>
        @keyframes shine {
            0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
            100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
        }
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _display_input_section(self):
        """Display structured input section for locations using Streamlit defaults"""
        st.markdown('<div style="display: flex; justify-content: center; align-items: center; gap: 20px; margin: 20px 0; font-size: 1.1em;">🏢Enter Warehouse Location →📍Enter Delivery Points  →  🚀Get Optimized Route</div>', unsafe_allow_html=True)
        
        # Warehouse Section
        self._display_warehouse_section()
        
        st.markdown("---")
        
        # Delivery Locations Section
        self._display_delivery_locations_section()
    
    def _display_warehouse_section(self):
        """Display warehouse input section with enhanced Streamlit styling"""
        st.subheader("🏢 Warehouse Location")
        
        # Create a card-like container for warehouse input
        with st.container():
            # Input section with full width
            warehouse = st.text_input(
                "📍 Enter Warehouse Address",
                value=st.session_state.warehouse,
                placeholder="e.g., Chennai Central, Mumbai Port, Delhi Warehouse",
                key="warehouse_input",
                help="This is the starting point for all delivery routes",
                label_visibility="visible"
            )
            
            # Auto-geocode when warehouse changes
            if warehouse != st.session_state.warehouse:
                st.session_state.warehouse = warehouse
                if warehouse and warehouse.strip():
                    self._auto_geocode_warehouse()
                else:
                    st.session_state.warehouse_coords = None
        
        # Display warehouse information using Streamlit's default components
        if st.session_state.warehouse and st.session_state.warehouse_coords:
            with st.expander("📍 Warehouse Details", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🏢 Location", st.session_state.warehouse)
                with col2:
                    lat, lon = st.session_state.warehouse_coords
                    st.metric("📍 Coordinates", f"{lat:.4f}, {lon:.4f}")
    
    def _auto_geocode_warehouse(self):
        """Automatically geocode warehouse when input changes"""
        if not st.session_state.warehouse or not st.session_state.warehouse.strip():
            return
        
        try:
            coords = self.geocoder.geocode_address(st.session_state.warehouse)
            if coords:
                st.session_state.warehouse_coords = coords
            else:
                st.session_state.warehouse_coords = None
        except Exception:
            st.session_state.warehouse_coords = None
    
    def _display_delivery_locations_section(self):
        """Display dynamic delivery locations management section with enhanced Streamlit styling"""
        st.subheader("📦 Delivery Locations")
        
        # Add new location using number selector and dynamic input fields
        st.write("📍 Add Delivery Locations")
        
        # Number selector for delivery points
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            num_locations = st.number_input(
                "Select Number of Delivery Points",
                min_value=1,
                max_value=20,
                value=1,
                step=1,
                key="num_delivery_points"
            )
        
        with col2:
            st.write("")  # Empty space for alignment
        
        with col3:
            st.write("")  # Empty space for alignment
        
        # Only show input fields after number is explicitly changed (not initially)
        # Check if user has actually selected a number (different from default)
        current_num = st.session_state.get("num_delivery_points", 1)
        if current_num > 1:  # Only show if user selected more than 1
            # Dynamic input fields based on number selected
            for i in range(num_locations):
                col1, col2 = st.columns([4, 2])
                
                with col1:
                    location_name = st.text_input(
                        f"📍 Location {i+1}",
                        placeholder=f"e.g., T Nagar, Adyar, Velachery",
                    key=f"delivery_location_{i}",
                    help="Enter delivery address"
                )
                
                # Auto-geocode when location changes
                if location_name and location_name.strip():
                    if location_name not in st.session_state.delivery_locations:
                        if location_name != st.session_state.warehouse:
                            # Auto-geocode and add to list
                            coords = self.geocoder.geocode_address(location_name)
                            if coords:
                                st.session_state.delivery_locations.append(location_name)
                                st.session_state.geocoded_locations[location_name] = coords
                                st.session_state.input_counter = st.session_state.get('input_counter', 0) + 1
                                st.rerun()
            
            with col2:
                # Display coordinates if available, aligned with input field
                if location_name in st.session_state.geocoded_locations:
                    coords = st.session_state.geocoded_locations[location_name]
                    st.markdown(f'<div style="margin-top: 28px; padding: 8px; background-color: #e3f2fd; border-radius: 4px; color: #1565c0; font-size: 14px;">📍 {coords[0]:.4f}, {coords[1]:.4f}</div>', unsafe_allow_html=True)
                elif location_name and location_name.strip():
                    st.markdown(f'<div style="margin-top: 28px; padding: 8px; background-color: #fff3cd; border-radius: 4px; color: #856404; font-size: 14px;">🔄 Processing...</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="margin-top: 28px;">&nbsp;</div>', unsafe_allow_html=True)
            
            # Clear all button - only show after input fields are displayed
            if st.button("🗑️ Clear All Locations", use_container_width=True, help="Remove all delivery locations"):
                self._clear_all_delivery_locations()
        
        # Display delivery locations using enhanced Streamlit components
        self._display_delivery_locations_streamlit()
    
    def _add_delivery_location_dynamic(self, location):
        """Add delivery location with real-time geocoding"""
        if not location or not location.strip():
            st.warning("⚠️ Please enter a location")
            return
        
        location = location.strip()
        
        if location in st.session_state.delivery_locations:
            st.warning("⚠️ Location already added")
            return
        
        if location == st.session_state.warehouse:
            st.warning("⚠️ Delivery location cannot be same as warehouse")
            return
        
        # Real-time geocoding
        with st.spinner(f"🔄 Adding {location}..."):
            coords = self.geocoder.geocode_address(location)
            
            if coords:
                st.session_state.delivery_locations.append(location)
                st.session_state.geocoded_locations[location] = coords
                st.success(f"✅ Added: {location}")
                # Increment counter to refresh input field
                st.session_state.input_counter = st.session_state.get('input_counter', 0) + 1
                st.rerun()
            else:
                st.error(f"❌ Could not geocode: {location}")
                return
    
    def _clear_all_delivery_locations(self):
        """Clear all delivery locations"""
        if st.session_state.delivery_locations:
            st.session_state.delivery_locations = []
            st.session_state.geocoded_locations = {}
            st.success("🗑️ All delivery locations cleared")
            st.rerun()
    
    def _display_delivery_locations_streamlit(self):
        """Display delivery locations in tabular format"""
        if not st.session_state.delivery_locations:
            st.info("📍 No delivery locations added yet, Add Delivery Locations above to get started.")
            return
        
        # Enhanced summary metrics with better styling
        geocoded_count = len([loc for loc in st.session_state.delivery_locations 
                           if loc in st.session_state.geocoded_locations])
        total_count = len(st.session_state.delivery_locations)
        
        # Display delivery locations in tabular format
        st.write("### 🗺️ Delivery Locations")
        
        # Prepare data for st.dataframe
        table_data = []
        for i, location in enumerate(st.session_state.delivery_locations):
            coordinates_str = "N/A"
            status = "⏳ Not Geocoded"
            
            if location in st.session_state.geocoded_locations:
                coords = st.session_state.geocoded_locations[location]
                coordinates_str = f"{coords[0]:.6f}, {coords[1]:.6f}"
                status = "✅ Geocoded"
            
            table_data.append({
                "Address": location,
                "Coordinates": coordinates_str,
                "Status": status
            })

        if table_data:
            df = pd.DataFrame(table_data)
            # Ensure all columns are strings to prevent Arrow serialization errors
            for col in df.columns:
                df[col] = df[col].astype(str)
            st.dataframe(df, use_container_width=True, hide_index=True)

        # Action buttons removed - table only display
        
        # Progress indicator
        if geocoded_count == total_count and total_count > 0:
            st.success("🎯 All locations geocoded and ready for route optimization!")
        elif geocoded_count > 0:
            st.info(f"📍 {geocoded_count}/{total_count} locations ready. {total_count - geocoded_count} locations pending geocoding.")
    
    def _remove_single_location(self, location):
        """Remove a specific delivery location"""
        if location in st.session_state.delivery_locations:
            st.session_state.delivery_locations.remove(location)
            if location in st.session_state.geocoded_locations:
                del st.session_state.geocoded_locations[location]
            st.success(f"🗑️ Removed: {location}")
            st.rerun()
    
    def _retry_geocode_location(self, location):
        """Retry geocoding a specific location"""
        with st.spinner(f"🔄 Geocoding {location}..."):
            coords = self.geocoder.geocode_address(location)
            if coords:
                st.session_state.geocoded_locations[location] = coords
                st.success(f"✅ Geocoded: {location}")
                st.rerun()
            else:
                st.error(f"❌ Could not geocode: {location}")
    
    def _remove_delivery_location(self, index):
        """Remove a specific delivery location"""
        if 0 <= index < len(st.session_state.delivery_locations):
            location = st.session_state.delivery_locations[index]
            st.session_state.delivery_locations.pop(index)
            if location in st.session_state.geocoded_locations:
                del st.session_state.geocoded_locations[location]
            st.success(f"🗑️ Removed: {location}")
            st.rerun()
    
    def _display_optimization_button(self):
        """Display enhanced route optimization button"""
        st.markdown("---")
        
        # Validation check
        can_optimize = (
            st.session_state.warehouse and 
            st.session_state.warehouse_coords and 
            st.session_state.delivery_locations and
            len([loc for loc in st.session_state.delivery_locations 
                 if loc in st.session_state.geocoded_locations]) > 0
        )
        
        # Center the optimization button with better styling
        with st.container():
            if can_optimize:
                # Enhanced button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🚀 Optimize Route", type="primary", use_container_width=True, 
                               help="Generate the most efficient delivery route using Dijkstra's algorithm"):
                        self._optimize_route()
            else:
                # Show what's missing
                st.warning("⚠️ Complete the setup before optimizing:")
                
                if not st.session_state.warehouse:
                    st.write("❌ Add a warehouse location")
                elif not st.session_state.warehouse_coords:
                    st.write("❌ Warehouse needs to be geocoded")
                
                if not st.session_state.delivery_locations:
                    st.write("❌ Add delivery locations")
                else:
                    geocoded_count = len([loc for loc in st.session_state.delivery_locations 
                                       if loc in st.session_state.geocoded_locations])
                    if geocoded_count < len(st.session_state.delivery_locations):
                        st.write(f"❌ {len(st.session_state.delivery_locations) - geocoded_count} delivery locations need geocoding")
                
                # Disabled button with message
                st.button("🚀 Optimize Route", type="primary", use_container_width=True, disabled=True)
    
    def _optimize_route(self):
        """Main route optimization logic using pre-geocoded coordinates"""
        # Validate inputs
        if not st.session_state.warehouse:
            st.error("❌ Please enter a warehouse location")
            return
        
        if not st.session_state.delivery_locations:
            st.error("❌ Please add at least one delivery location")
            return
        
        # Check if warehouse is geocoded
        if not st.session_state.warehouse_coords:
            st.error("❌ Please geocode the warehouse location first")
            return
        
        # Check if all delivery locations are geocoded
        non_geocoded = [loc for loc in st.session_state.delivery_locations 
                       if loc not in st.session_state.geocoded_locations]
        if non_geocoded:
            st.error(f"❌ Please geocode these locations first: {', '.join(non_geocoded)}")
            return
        
        try:
            with st.spinner("🚀 Optimizing route with pre-geocoded coordinates..."):
                # Step 1: Use pre-geocoded coordinates
                coordinates = {st.session_state.warehouse: st.session_state.warehouse_coords}
                coordinates.update(st.session_state.geocoded_locations)
                
                # Step 2: Calculate distance matrix
                distance_matrix = self.distance_calculator.calculate_distance_matrix(coordinates)
                
                # Step 3: Build graph
                graph = GraphBuilder.build_location_graph(coordinates, distance_matrix)
                
                # Step 4: Run Dijkstra's algorithm
                optimizer = DijkstraOptimizer(graph)
                optimization_results = optimizer.optimize_delivery_route(
                    st.session_state.warehouse,
                    st.session_state.delivery_locations
                )
                
                # Step 5: Create visualization map
                route_map = self.map_visualizer.create_route_map(
                    coordinates,
                    optimization_results['optimized_route'],
                    distance_matrix,
                    st.session_state.warehouse
                )
                
                # Store results in session state
                st.session_state.optimized_route = optimization_results
                st.session_state.route_map = route_map
                st.session_state.coordinates = coordinates
                st.session_state.distance_matrix = distance_matrix
                
                st.success("✅ Route optimized successfully!")
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error during optimization: {str(e)}")
    
    def _display_results(self):
        """Display optimization results"""
        if not st.session_state.optimized_route:
            return
        
        st.markdown("---")
        st.markdown('<h2 style="text-align: center;" class="section-header">🎯 Optimization Results</h2>', 
                   unsafe_allow_html=True)
        
        # Display optimized route
        self._display_optimized_route()
        
        # Display map
        self._display_map()
        
        # Display analytics (now below map)
        self._display_analytics()
        
        # Add delivery boy quote first
        st.markdown("---")
        st.markdown('<div style="text-align: center; margin: 2rem 0;"><p style="font-size: 1.2em; color: #666; font-style: italic; font-family: \'Times New Roman\', serif;">Have a safe and smooth delivery journey! Every package you deliver brings a smile to someone\'s face🚚</p></div>', unsafe_allow_html=True)
        
        # Add Start New Route button at the end
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Start New Route", type="primary", use_container_width=True, help="Clear all data and start a new route"):
                self._start_new_route()
    
    def _start_new_route(self):
        """Clear all data and start a new route"""
        # Clear all session state data
        st.session_state.warehouse = ""
        st.session_state.delivery_locations = []
        st.session_state.location_input = ""
        st.session_state.optimized_route = None
        st.session_state.route_map = None
        st.session_state.geocoded_locations = {}
        st.session_state.warehouse_coords = None
        st.session_state.input_counter = 0
        
        st.success("🔄 Ready for new route! All data has been cleared.")
        st.rerun()
    
    def _display_optimized_route(self):
        st.subheader("🛣️ Optimized Round Trip Route")
        
        route = st.session_state.optimized_route['optimized_route']
        total_distance = st.session_state.optimized_route['total_distance']
        is_round_trip = st.session_state.optimized_route.get('is_round_trip', False)
        
        # Route type indicator
        if is_round_trip:
            st.success("🔄 Round Trip Route: Warehouse → Deliveries → Warehouse")
        
        # Route sequence as flow chart
        st.write("**Route Sequence:**")
        
        # Create flow chart HTML with enhanced styling
        flow_html = '<div style="display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 15px; margin: 25px 0; font-family: \'Times New Roman\', serif;">'
        
        for i, location in enumerate(route):
            if location == route[0] and i == 0:
                flow_html += f'<div style="background: #FF4B4B; color: white; padding: 12px 20px; border-radius: 12px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3); border: 2px solid #E53E3E; transition: all 0.3s ease; transform: translateY(0); font-family: \'Times New Roman\', serif;">🏢 {location}</div>'
            elif location == route[-1] and i == len(route) - 1 and location == route[0]:
                flow_html += f'<div style="background: #FF4B4B; color: white; padding: 12px 20px; border-radius: 12px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3); border: 2px solid #E53E3E; transition: all 0.3s ease; transform: translateY(0); font-family: \'Times New Roman\', serif;">🏢 {location}</div>'
            else:
                flow_html += f'<div style="background: #1A1A1A; color: white; padding: 12px 20px; border-radius: 12px; font-size: 16px; box-shadow: 0 4px 15px rgba(26, 26, 26, 0.3); border: 2px solid #000000; transition: all 0.3s ease; transform: translateY(0); font-family: \'Times New Roman\', serif;">📦 {location}</div>'
            
            # Add enhanced arrow between points (except after last point)
            if i < len(route) - 1:
                flow_html += '<div style="font-size: 24px; color: #718096; font-weight: bold; text-shadow: 0 2px 4px rgba(113, 128, 150, 0.3); animation: pulse 2s infinite; font-family: \'Times New Roman\', serif;">→</div>'
        
        flow_html += '</div>'
        st.markdown(flow_html, unsafe_allow_html=True)
        
        # Route statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            delivery_count = st.session_state.optimized_route['delivery_count']
            st.metric(
                label="📍 Total Stops",
                value=delivery_count
            )
        
        with col2:
            st.metric(
                label="📏 Total Estimated Distance",
                value=f"{total_distance:.2f} km"
            )
        
        with col3:
            # Calculate estimated time (using average speed)
            from analytics import DeliveryAnalytics
            analytics = DeliveryAnalytics()
            time_metrics = analytics.calculate_delivery_time(total_distance, delivery_count)
            st.metric(
                label="⏱️ Total Estimated Time (Hrs)",
                value=f"{time_metrics['total_time_hours']:.1f}"
            )
        
        with col4:
            # Calculate fuel required
            fuel_metrics = analytics.calculate_fuel_consumption(total_distance)
            st.metric(
                label="⛽ Fuel Required (L)",
                value=f"{fuel_metrics['fuel_liters']:.1f}"
            )
        
        # Show nearest order if available
        if 'nearest_order' in st.session_state.optimized_route:
            nearest_order = st.session_state.optimized_route['nearest_order']
            st.write("**Delivery Order (Nearest → Farthest):**")
            order_text = " → ".join(nearest_order)
            st.markdown(f'<div style="background: #e3f2fd; padding: 0.75rem; border-radius: 0.5rem; border-left: 4px solid #2196f3; color: #1565c0; font-weight: bold; font-size: 1.1em;">{order_text}</div>', unsafe_allow_html=True)
    
    def _display_analytics(self):
        """Display delivery analytics"""
        if not st.session_state.optimized_route:
            return
        
        total_distance = st.session_state.optimized_route['total_distance']
        delivery_count = st.session_state.optimized_route['delivery_count']
        
        self.analytics.display_analytics_dashboard(
            total_distance,
            delivery_count,
            st.session_state.optimized_route
        )
    
    def _display_map(self):
        """Display the route map"""
        st.subheader("🗺️ Route Visualization")
        
        if st.session_state.route_map:
            self.map_visualizer.display_map(st.session_state.route_map, height=600)
        else:
            st.error("❌ Unable to generate map")
        
        # Display detailed breakdown table below map
        self._display_detailed_breakdown_table()
    
    def _display_detailed_breakdown_table(self):
        """Display detailed breakdown in tabular format"""
        st.subheader("📋 Detailed Breakdown")
        
        route = st.session_state.optimized_route['optimized_route']
        total_distance = st.session_state.optimized_route['total_distance']
        coordinates = st.session_state.coordinates
        distance_matrix = st.session_state.distance_matrix
        
        # Create detailed breakdown data
        breakdown_data = []
        
        for i, location in enumerate(route):
            if i == 0:
                location_type = "Warehouse (Start)"
                icon = "🏢"
            elif i == len(route) - 1 and location == route[0]:
                location_type = "Warehouse (End)"
                icon = "🏢"
            else:
                location_type = "Delivery Point"
                icon = "📦"
            
            # Calculate distance to next point
            if i < len(route) - 1:
                next_location = route[i + 1]
                segment_distance = distance_matrix[location][next_location]
            else:
                segment_distance = 0
            
            breakdown_data.append({
                "Stop": i + 1,
                "Location": f"{icon} {location}",
                "Type": location_type,
                "Distance to Next (km)": f"{segment_distance:.2f}" if segment_distance > 0 else "N/A",
                "Coordinates": f"{coordinates[location][0]:.4f}, {coordinates[location][1]:.4f}"
            })
        
        # Display as table
        df_breakdown = pd.DataFrame(breakdown_data)
        # Ensure all columns are strings to prevent Arrow serialization errors
        for col in df_breakdown.columns:
            df_breakdown[col] = df_breakdown[col].astype(str)
        st.dataframe(df_breakdown, use_container_width=True, hide_index=True)


def main():
    """Main function to run the application"""
    app = DeliveryRouteApp()
    app.run()


if __name__ == "__main__":
    main()
