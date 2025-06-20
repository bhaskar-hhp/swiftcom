import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime


# --- Clear cached data ---
st.cache_data.clear()

# --- Page config ---
st.set_page_config(page_title="Model Manager", page_icon="🛠️")

# --- Connect to DB ---
db_path = os.path.join(os.getcwd(), "data.db")

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

# --- Create tables if not exist ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    type TEXT,
    pass TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT,
    model TEXT,
    color TEXT,
    specs TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    address TEXT,
    location TEXT,
    contact TEXT,
    email TEXT,
    added_by TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS po (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    time TEXT,
    dist TEXT,
    location TEXT,
    model TEXT,
    color TEXT,
    spec TEXT,
    quantity INTEGER,
    status TEXT,
    remark TEXT,
    added_by TEXT,
    update_by TEXT
)
""")

conn.commit()

# --- Initialize session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "usertype" not in st.session_state:
    st.session_state.usertype = ""
if "page" not in st.session_state:
    st.session_state.page = None

# --- Login section ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("SELECT * FROM users WHERE name = ? AND pass = ?", (username.strip().upper(), password))
        user = cursor.fetchone()
        if user:
            st.session_state.logged_in = True
            st.session_state.username = user[1]
            st.session_state.usertype = user[2]
            st.success(f"Welcome {user[1]}! You are logged in as {user[2]}.")
            st.rerun()
        else:
            st.error("Invalid credentials. Try again.")

# --- After login ---
if st.session_state.logged_in:
    st.sidebar.image("logo.png", use_container_width=True)
    st.sidebar.title("Navigation")
    st.sidebar.success(f"Logged in as: {st.session_state.username} ({st.session_state.usertype})")

    if st.session_state.usertype == "Admin":
        st.session_state.page = st.sidebar.radio(
            "Choose page",
            [
                "📦 Dashboard", 
                "👤 Add User", 
                "🗑️ Delete User", 
                "➕ Add/Delete Model", 
                "🏪 Add/Delete Distributor",
                "Create Order",
                "Update Order"
            ]
        )
    elif st.session_state.usertype == "Standard":
        st.session_state.page = st.sidebar.radio(
            "Choose page",
            [
                "📦 Dashboard", 
                "Create Order",
                "Update Order"
            ]
        )
    elif st.session_state.usertype == "Guest":
        st.session_state.page = st.sidebar.radio(
            "Choose page",
            [
                "📦 Dashboard", 
                "Create Order"
            ]
        )
    elif st.session_state.usertype == "Back Office":
        st.session_state.page = st.sidebar.radio(
            "Choose page",
            [
                "📦 Dashboard", 
                "Create Order",
                "Update Order"
            ]
        )
    
    else:
        st.session_state.page = st.sidebar.radio(
            "Choose page",
            [
                "📦 Dashboard",
            

            ]
        )

    # --- Logout ---
    if st.sidebar.button("Logout"):
        for key in ["logged_in", "username", "usertype", "page"]:
            st.session_state.pop(key, None)
        st.rerun()

    # --- Pages ---

    # View Users
    if st.session_state.page == "📦 Dashboard":
        st.title("All Users")
        df = pd.read_sql_query("SELECT * FROM users", conn)
        st.dataframe(df, use_container_width=True)

        st.title("All Distributors")
        df = pd.read_sql_query("SELECT * FROM dist", conn)
        st.dataframe(df, use_container_width=True)

        st.title("All Models")
        df = pd.read_sql_query("SELECT * FROM models", conn)
        st.dataframe(df, use_container_width=True)
 
    # add user
    elif st.session_state.page == "👤 Add User":
        st.title("All Users")
        df = pd.read_sql_query("SELECT * FROM users", conn)
        st.dataframe(df, use_container_width=True)
        st.title("Add New User")
        with st.form("add_form"):
            name = st.text_input("Enter User Name: ").strip().upper()
            user_type = st.selectbox("User Type", ["Admin", "Standard", "Guest", "Back Office"])
            password = st.text_input("Create Password", type="password")
            submit = st.form_submit_button("Add")

            if submit:
                if not name or not password:
                    st.warning("Please provide both a name and a password.")
                else:
                    cursor.execute("INSERT INTO users (name, type, pass) VALUES (?, ?, ?)", (name, user_type, password))
                    conn.commit()
                    st.success(f"User '{name}' added!")
                    st.rerun()

        st.markdown("---")
        with open("add-bulk.csv", "rb") as f:
            st.download_button("📥 Download CSV Format", data=f, file_name="add-bulk.csv", mime="text/csv")

        st.subheader("📂 Upload CSV to Add Users in Bulk")
        csv_file = st.file_uploader("Upload a CSV file with columns: name, type, pass", type="csv")

        if csv_file and "processed_bulk_upload" not in st.session_state:
            try:
                df = pd.read_csv(csv_file)
                df.columns = df.columns.str.lower()
                df["name"] = df["name"].str.strip().str.upper()
                for _, row in df.iterrows():
                    cursor.execute("INSERT INTO users (name, type, pass) VALUES (?, ?, ?)",
                                (row["name"], row["type"], row["pass"]))
                conn.commit()
                st.success(f"{len(df)} users added successfully!")
                st.session_state.processed_bulk_upload = True
            except Exception as e:
                st.error(f"Error processing file: {e}")
    ## delete user
    elif st.session_state.page == "🗑️ Delete User":
        st.title("Delete a User")
        df = pd.read_sql_query("SELECT * FROM users", conn)

        if df.empty:
            st.info("No users found.")
        else:
            st.dataframe(df)
            selected_id = st.selectbox("Select User ID to Delete", df["id"])
            selected_user = df[df["id"] == selected_id]
            st.write("Selected User:")
            st.table(selected_user)

            if st.button("Delete"):
                cursor.execute("DELETE FROM users WHERE id = ?", (selected_id,))
                conn.commit()
                st.success(f"User with ID {selected_id} deleted.")
                st.rerun()

        confirm_reset = st.checkbox("Are you sure you want to delete all Users?")
        if st.button("Reset All Users Data"):
            if confirm_reset:
                cursor.execute("DELETE FROM users")
                conn.commit()
                st.success("All users have been deleted.")
                st.rerun()
            else:
                st.info("Please check the box to confirm before resetting the Users.", icon="⚠️")
    
    #add model
    elif st.session_state.page == "➕ Add/Delete Model":
        st.title("📋 Existing Models")
        df_models = pd.read_sql_query("SELECT * FROM models", conn)
        if df_models.empty:
            st.info("No models added yet.")
        else:
            st.dataframe(df_models, use_container_width=True)

        st.markdown("---")
        st.title("➕ Add New Model")

        # Add model form
        with st.form("add_model_form"):
            all_brands = df_models["brand"].unique().tolist()
            custom_brand = st.text_input("Or type a new brand (If Brand not in list)")
            selected_brand = st.selectbox("Select a brand", all_brands)

            brand = custom_brand if custom_brand else selected_brand
            model = st.text_input("Model Name")
            color = st.text_input("Color")
            specs = st.text_area("Specifications")
            submit = st.form_submit_button("Add Model")

            if submit:
                if not brand or not model or not color or not specs:
                    st.warning("Please fill in all fields.")
                else:
                    cursor.execute("INSERT INTO models (brand, model, color, specs) VALUES (?, ?, ?, ?)", (brand, model, color, specs))
                    conn.commit()
                    st.success(f"Model '{model}' added successfully!")
                    st.rerun()
        # Download CSV template
        model_template = pd.DataFrame(columns=["brand", "model", "color", "specs"])
        st.download_button("📥 Download Model CSV Template", model_template.to_csv(index=False).encode(), "model-template.csv", "text/csv")
        # Upload CSV
        st.subheader("📂 Upload CSV to Add Models in Bulk")
        csv_model_file = st.file_uploader("Upload CSV with columns: model, color, specs", type="csv")
        # Process CSV
        if csv_model_file and "processed_bulk_upload_models" not in st.session_state:
            try:
                df = pd.read_csv(csv_model_file)
                df.columns = df.columns.str.lower()
                for _, row in df.iterrows():
                    cursor.execute("INSERT INTO models (brand, model, color, specs) VALUES (?, ?, ?, ?)",
                                (row["brand"], row["model"], row["color"], row["specs"]))
                conn.commit()
                st.success(f"{len(df)} models added successfully!")
                st.session_state.processed_bulk_upload_models = True
            except Exception as e:
                st.error(f"Error uploading models: {e}")
        # Delete model
        st.markdown("---")
        st.subheader("🗑️ Delete a Model Entry")

        # Smart select or input for Brand
        brands = df_models["brand"].unique().tolist()

        if "selected_brand" not in st.session_state:
            st.session_state.selected_brand = ""
        if "custom_brand" not in st.session_state:
            st.session_state.custom_brand = ""

        def on_select_brand():
            st.session_state.custom_brand = ""

        def on_custom_brand():
            st.session_state.selected_brand = ""

        st.selectbox("Select Existing Brand", options=[""] + brands, key="selected_brand", on_change=on_select_brand)
        

        # Use typed brand if provided, else selected
        brand = st.session_state.custom_brand.strip() if st.session_state.custom_brand.strip() else st.session_state.selected_brand

        if brand:
            filtered_by_brand = df_models[df_models["brand"] == brand]
            models = filtered_by_brand["model"].unique().tolist()

            if models:
                selected_model = st.selectbox("Select Model", models)
                filtered_by_model = filtered_by_brand[filtered_by_brand["model"] == selected_model]

                colors = filtered_by_model["color"].unique().tolist()
                selected_color = st.selectbox("Select Color", colors)

                filtered_by_color = filtered_by_model[filtered_by_model["color"] == selected_color]
                specs = filtered_by_color["specs"].unique().tolist()
                selected_specs = st.selectbox("Select Specifications", specs)

                if st.button("Delete Selected Model Entry"):
                    cursor.execute(
                        "DELETE FROM models WHERE brand = ? AND model = ? AND color = ? AND specs = ?",
                        (brand, selected_model, selected_color, selected_specs)
                    )
                    conn.commit()
                    st.success(f"Deleted model: {brand} / {selected_model} / {selected_color}")
                    st.rerun()
            else:
                st.info("No models found for selected brand.")
        else:
            st.warning("Please select or type a brand.")

            # Reset Table Option
            st.markdown("---")
            confirm_reset = st.checkbox("Are you sure you want to delete all models?")
            if st.button("Reset Models Table"):
                if confirm_reset:
                    cursor.execute("DELETE FROM models")
                    conn.commit()
                    st.success("All models have been deleted.")
                    st.rerun()
                else:
                    st.info("Please check the box to confirm before resetting the models.", icon="⚠️")

        # Distribuutor page - Display Existing Distributors
    elif st.session_state.page == "🏪 Add/Delete Distributor":
        st.title("📋 Existing Distributors")    
        df_dist = pd.read_sql_query("SELECT * FROM dist", conn)
        if df_dist.empty:
            st.info("No distributors available.")
        else:
            st.dataframe(df_dist, use_container_width=True)

            dist_ids = df_dist["id"].tolist()
            dist_id_to_delete = st.selectbox("Select Distributor ID to Delete", dist_ids)

            if st.button("Delete Selected Distributor"):
                cursor.execute("SELECT name FROM dist WHERE id = ?", (dist_id_to_delete,))
                dist_name = cursor.fetchone()[0]
                cursor.execute("DELETE FROM dist WHERE id = ?", (dist_id_to_delete,))
                cursor.execute("DELETE FROM users WHERE name = ? AND type = 'Guest'", (dist_name,))
                conn.commit()
                st.success("Distributor and corresponding Guest user deleted.")
                st.rerun()
        # Add Distributor form
        st.markdown("---")
        st.title("➕ Add Distributor")

        with st.form("add_distributor_form"):
            col1, col2 = st.columns(2)
            with col1:
                dist_name = st.text_input("Distributor Name").strip().upper()
                location = st.text_input("Location").strip().title()
                contact = st.text_input("Contact Number").strip()
            with col2:
                address = st.text_area("Address").strip().title()
                email = st.text_input("Email").strip()

            submit = st.form_submit_button("Add Distributor")

            if submit:
                if not dist_name or not address or not location or not contact or not email:
                    st.warning("Please fill in all fields.")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO dist (name, address, location, contact, email, added_by)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (dist_name, address, location, contact, email, st.session_state.username))
                        
                        cursor.execute("""
                            INSERT INTO users (name, type, pass) VALUES (?, 'Guest', '1234')
                        """, (dist_name,))
                        
                        conn.commit()
                        st.success(f"Distributor '{dist_name}' added with Guest login.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding distributor: {e}")
    # Create Order
    elif st.session_state.page == "Create Order":
        st.header("📦 Create Order")

        # Get locations
        cursor.execute("SELECT DISTINCT location FROM dist")
        locations = [row[0] for row in cursor.fetchall()]
        selected_location = st.selectbox("Select Location", locations)

        # Filtered distributors
        cursor.execute("SELECT name FROM dist WHERE location = ?", (selected_location,))
        distributors = [row[0] for row in cursor.fetchall()]
        selected_dist = st.selectbox("Select Distributor", distributors)

        # filtered brands then models, colors, specs
        df_models = pd.read_sql_query("SELECT * FROM models", conn)
        brands = df_models["brand"].unique().tolist()

        if "selected_brand" not in st.session_state:
            st.session_state.selected_brand = ""
        if "custom_brand" not in st.session_state:
            st.session_state.custom_brand = ""

        def on_select_brand():
            st.session_state.custom_brand = ""

        def on_custom_brand():
            st.session_state.selected_brand = ""

        st.selectbox("Select Existing Brand", options=[""] + brands, key="selected_brand", on_change=on_select_brand)
        

        # Use typed brand if provided, else selected
        brand = st.session_state.custom_brand.strip() if st.session_state.custom_brand.strip() else st.session_state.selected_brand

        if brand:
            filtered_by_brand = df_models[df_models["brand"] == brand]
            models = filtered_by_brand["model"].unique().tolist()

            if models:
                selected_model = st.selectbox("Select Model", models)
                filtered_by_model = filtered_by_brand[filtered_by_brand["model"] == selected_model]

                colors = filtered_by_model["color"].unique().tolist()
                selected_color = st.selectbox("Select Color", colors)

                filtered_by_color = filtered_by_model[filtered_by_model["color"] == selected_color]
                specs = filtered_by_color["specs"].unique().tolist()
                selected_specs = st.selectbox("Select Specifications", specs)

        quantity = st.number_input("Quantity", min_value=1, step=1)

        if st.button("Create Order"):
            now = datetime.now()
            date = now.strftime("%d-%m-%Y")
            time = now.strftime("%H:%M:%S")
            status = "New"
            remark = ""
            added_by = st.session_state["username"]
            update_by = added_by

            cursor.execute("""
                INSERT INTO po (date, time, dist, location, model, color, spec, quantity, status, remark, added_by, update_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (date, time, selected_dist, selected_location, selected_model, selected_color, selected_specs, quantity, status, remark, added_by, update_by))
            conn.commit()
            st.success("✅ Order created successfully!")
<<<<<<< HEAD
            st.toast("Saved successfully! ✅")
            #st.snow()  
            st.balloons()   
    
    # -----------Upate Order page --------------  
    # ----------- Update Order page --------------  
    if st.session_state.page == "Update Order":
        st.title("📦 Update Orders")
        if st.button("🔄 Refresh"):
            st.rerun()

        status_options = ["New", "Processing", "Biling Done", "Dispatched", "Delivered", "Cancelled"]
        selected_status = st.radio("Select Order Status to Filter", status_options, horizontal=True)

        # Date range filter for Delivered and Cancelled
        date_filter_applied = False
        if selected_status in ["Delivered", "Cancelled"]:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
            date_filter_applied = True
            # Format dates as dd-mm-yyyy
            formatted_start = start_date.strftime("%d-%m-%Y")
            formatted_end = end_date.strftime("%d-%m-%Y")

        # Build query with optional date range
        base_query = "SELECT * FROM po WHERE status = ?"
        params = [selected_status]

        if date_filter_applied:
            base_query += " AND date BETWEEN ? AND ?"
            params.extend([formatted_start, formatted_end])
            st.markdown(f"🗓️ Start Date: **{formatted_start}**")
            st.markdown(f"🗓️ End Date: **{formatted_end}**")

        df_orders = pd.read_sql_query(base_query, conn, params=params)

        if df_orders.empty:
            st.info(f"No orders with status '{selected_status}' found.")
        else:
            # Filter by distributor
            dist_names = df_orders["dist"].unique().tolist()
            selected_dist = st.selectbox("Select Distributor", dist_names)

            df_filtered = df_orders[df_orders["dist"] == selected_dist]

            # ✅ Show reduced view using st.data_editor
            display_cols = ["id", "location", "model", "color", "spec", "quantity"]
            st.subheader("Orders for Selected Distributor")
            st.data_editor(
                df_filtered[display_cols],
                use_container_width=True,
                disabled=True,  # Read-only
                hide_index=True
            )

            # 🔽 Download full dataset (all columns)
            csv_data = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download All Order Details (CSV)", data=csv_data, file_name="orders_full.csv", mime="text/csv")
=======
            #st.toast("Saved successfully! ✅")
            #st.snow()  
            st.balloons()   
    # Update Order    
    elif st.session_state.page == "Update Order":
    
        st.header("🛠️ Update Order")

        # Step 1: Select Status
        status_options = [
            "🆕 New", "⚙️ Processing", "💳 Biling Done", 
            "🚚 Dispatched", "📦 Delivered", "❌ Cancelled"
        ]
        selected_status = st.select_slider("Select Order Status Category", options=status_options)

        selected_status = st.select_slider("Select Order Status Category", status_options)

        # Step 2: Fetch orders with selected status
        cursor.execute("SELECT id, dist, model, status FROM po WHERE status = ?", (selected_status,))
        orders = cursor.fetchall()

        if not orders:
            st.info(f"No orders with status '{selected_status}'.")
        else:
            # Step 3: Get unique distributors from filtered orders
            distributors = sorted(set(o[1] for o in orders))
            selected_dist = st.selectbox("Filter by Distributor", distributors)

            # Step 4: Filter orders by selected distributor
            filtered_orders = [o for o in orders if o[1] == selected_dist]

            if not filtered_orders:
                st.warning(f"No orders for distributor '{selected_dist}' under status '{selected_status}'.")
            else:
                # Step 5: Select specific order
                options = [f"{o[0]} - {o[1]} - {o[2]} ({o[3]})" for o in filtered_orders]
                selected_idx = st.selectbox("Select Order", range(len(options)), format_func=lambda i: options[i])
                selected_id = filtered_orders[selected_idx][0]

                # Step 6: Show current status & remark
                cursor.execute("SELECT status, remark FROM po WHERE id = ?", (selected_id,))
                current_status, current_remark = cursor.fetchone()

                new_status = st.selectbox("Update Status", status_options, index=status_options.index(current_status))
                new_remark = st.text_area("Update Remark", value=current_remark)
>>>>>>> 28b2e84 (update)

            # Select and update order
            order_ids = df_filtered["id"].tolist()
            selected_order_id = st.selectbox("Select Order ID to Update", order_ids)
            selected_order = df_filtered[df_filtered["id"] == selected_order_id].iloc[0]

            with st.form("update_order_form"):
                new_status = st.selectbox("Update Status", status_options, index=status_options.index(selected_order["status"]))
                new_remark = st.text_area("Remark", value=selected_order["remark"] or "")
                col1, col2 = st.columns(2)
                with col1:
                    submit_update = st.form_submit_button("Update Order")
                with col2:
                    submit_all = st.form_submit_button("📝 Update All Orders")

                if submit_update:
                    cursor.execute("""
                        UPDATE po SET status = ?, remark = ?, update_by = ?
                        WHERE id = ?
                    """, (new_status, new_remark.strip(), st.session_state.username, selected_order_id))
                    conn.commit()
<<<<<<< HEAD
                    st.success(f"Order ID {selected_order_id} updated successfully!")
                    st.rerun()

                if submit_all:
                    ids_to_update = df_filtered["id"].tolist()
                    for oid in ids_to_update:
                        cursor.execute("""
                            UPDATE po SET status = ?, remark = ?, update_by = ?
                            WHERE id = ?
                        """, (new_status, new_remark.strip(), st.session_state.username, oid))
                    conn.commit()
                    st.success(f"✅ {len(ids_to_update)} orders updated successfully!")
                    st.rerun()


#else:
#    st.title("🏠 Home")
#    st.write("Welcome to the Model Manager dashboard.\n\nUse the sidebar to navigate through the application.")
=======
                    st.success("✅ Order updated successfully.")
                    st.balloons()  # Optional fun effect

    else:
        st.title("🏠 Home")
        st.write("Welcome to the Model Manager dashboard.\n\nUse the sidebar to navigate through the application.")
>>>>>>> 28b2e84 (update)

# --- Close DB connection ---
conn.close()
