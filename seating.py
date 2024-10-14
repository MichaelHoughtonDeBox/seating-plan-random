import streamlit as st
import pandas as pd
import random
from collections import defaultdict
import io

class SeatingPlanGenerator:
    def __init__(self, attendees_df, num_guests=7, num_tables=9, table_size=7):
        """
        Initializes the SeatingPlanGenerator with attendees DataFrame and seating parameters.
        
        :param attendees_df: pandas DataFrame containing Day 1 attendees.
        :param num_guests: Number of guest entries to add.
        :param num_tables: Total number of tables for Day 2.
        :param table_size: Number of seats per table.
        """
        self.attendees_df = attendees_df
        self.num_guests = num_guests
        self.num_tables = num_tables
        self.table_size = table_size
        self.guests = self.generate_guests()
    
    def generate_guests(self):
        """
        Generates a DataFrame of guest entries to be added to the Day 2 seating plan.
        
        :return: pandas DataFrame representing guest entries.
        """
        guests = []
        for i in range(1, self.num_guests + 1):
            guest = {
                "Table No.": "",
                "Seat No.": "",
                "Name": f"Guest {i}",
                "Business Title": "Guest",
                "City": "",
                "Business Line": "",
                "Sub Business Line": "",
                "Division": "",
                "Job Level": "",
                "Gender": "",
                "EWE Mgmt Team": "",
                "Workshop Facilitator": "N"
            }
            guests.append(guest)
        return pd.DataFrame(guests)
    
    def create_day2_seating(self):
        """
        Creates the Day 2 seating plan by mixing Day 1 attendees and adding guests.
        Ensures a mix of business lines and genders at each table.
        
        :return: pandas DataFrame representing Day 2 seating plan.
        """
        # Combine attendees and guests
        combined_df = pd.concat([self.attendees_df, self.guests], ignore_index=True)
        
        # Shuffle the combined attendees to randomize seating
        combined_df = combined_df.sample(frac=1).reset_index(drop=True)
        
        # Initialize tables using defaultdict
        tables = defaultdict(list)
        table_number = 1
        
        # Assign attendees to tables
        for index, attendee in combined_df.iterrows():
            tables[table_number].append(attendee)
            if len(tables[table_number]) == self.table_size:
                table_number += 1
            if table_number > self.num_tables:
                table_number = 1  # Loop back to the first table if necessary
        
        # Convert tables to DataFrame and assign Table No. and Seat No.
        day2_seating = []
        for table_no, members in tables.items():
            for seat_no, member in enumerate(members, start=1):
                member = member.copy()  # Create a copy to avoid modifying the original
                member["Table No."] = table_no
                member["Seat No."] = seat_no
                day2_seating.append(member)
        
        day2_df = pd.DataFrame(day2_seating)
        
        return day2_df
    
    def verify_seating_plan(self, day2_df):
        """
        Verifies that all Day 1 participants are included in Day 2 and there are no duplicates.
        
        :param day2_df: DataFrame containing the Day 2 seating plan.
        :return: tuple (bool, str) indicating if the plan is valid and an error message if not.
        """
        # Check for duplicates
        duplicates = day2_df[day2_df.duplicated(subset=['Name'], keep=False)]
        if not duplicates.empty:
            return False, f"Duplicate entries found: {', '.join(duplicates['Name'].unique())}"
        
        # Check if all Day 1 participants are included
        day1_names = set(self.attendees_df['Name'])
        day2_names = set(day2_df['Name'])
        missing_names = day1_names - day2_names
        if missing_names:
            return False, f"Missing participants from Day 1: {', '.join(missing_names)}"
        
        return True, "Seating plan is valid."

def main():
    """
    The main function that renders the Streamlit app.
    """
    st.title("Conference Seating Plan Generator - Day 2")
    st.write("""
    Upload the Day 1 seating plan CSV to generate a mixed Day 2 seating plan with 7 guests.
    """)

    # File uploader for Day 1 seating plan
    uploaded_file = st.file_uploader("Upload Day 1 Seating Plan (CSV)", type=["csv"])

    if uploaded_file is not None:
        try:
            # Read the uploaded CSV file into pandas DataFrame
            day1_df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            
            # Display Day 1 seating plan
            st.subheader("Day 1 Seating Plan")
            st.dataframe(day1_df)
            
            # Initialize the SeatingPlanGenerator
            generator = SeatingPlanGenerator(attendees_df=day1_df)
            
            # Use session state to store the current Day 2 seating plan
            if 'day2_df' not in st.session_state:
                st.session_state.day2_df = None
            
            # Button to generate or randomize Day 2 seating plan
            if st.button("Generate/Randomize Day 2 Seating Plan"):
                st.session_state.day2_df = generator.create_day2_seating()
                
                # Verify the seating plan
                is_valid, message = generator.verify_seating_plan(st.session_state.day2_df)
                if is_valid:
                    st.success(message)
                else:
                    st.error(message)
                    st.session_state.day2_df = None  # Reset the invalid seating plan
            
            # Display Day 2 seating plan if available and valid
            if st.session_state.day2_df is not None:
                st.subheader("Day 2 Seating Plan")
                st.dataframe(st.session_state.day2_df)
                
                # Convert Day 2 DataFrame to CSV for download
                csv_buffer = io.StringIO()
                st.session_state.day2_df.to_csv(csv_buffer, index=False)
                csv_bytes = csv_buffer.getvalue().encode('utf-8')
                
                st.download_button(
                    label="Download Day 2 Seating Plan CSV",
                    data=csv_bytes,
                    file_name='Table_Plan_Day_2.csv',
                    mime='text/csv'
                )
        
        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")
    else:
        st.info("Please upload a CSV file to begin.")

if __name__ == "__main__":
    main()