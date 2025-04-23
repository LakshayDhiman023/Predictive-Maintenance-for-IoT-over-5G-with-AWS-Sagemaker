import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import os

def generate_synthetic_data(n_samples=10000):
    """
    Generate synthetic CPU sensor data with labels and states.
    
    Parameters:
    n_samples (int): Number of data points to generate
    
    Returns:
    pd.DataFrame: DataFrame containing sensor data and labels
    """
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate sensor data with realistic ranges and correlations
    data = {
        'temperature': np.random.normal(70, 15, n_samples),  # Normal operating temp 70°C ± 15
        'voltage': np.random.normal(12, 1, n_samples),      # 12V ± 1V
        'current': np.random.normal(10, 2, n_samples),      # 10A ± 2A
        'cpu_usage': np.random.uniform(0, 100, n_samples),  # 0-100%
        'fan_speed': np.random.normal(2000, 500, n_samples) # 2000 RPM ± 500
    }
    
    df = pd.DataFrame(data)
    
    # Add correlations
    df['fan_speed'] = df['fan_speed'] + df['temperature'] * 10
    df['current'] = df['current'] + df['cpu_usage'] * 0.05
    
    # Create sensor labels (0: safe, 1: warning)
    df['temp_label'] = (df['temperature'] > 85).astype(int)
    df['voltage_label'] = ((df['voltage'] < 10) | (df['voltage'] > 14)).astype(int)
    df['current_label'] = (df['current'] > 13).astype(int)
    df['usage_label'] = (df['cpu_usage'] > 90).astype(int)
    df['fan_label'] = (df['fan_speed'] < 1500).astype(int)
    
    # Define CPU state (0: Normal, 1: Warning, 2: Critical)
    df['cpu_state'] = 0
    warning_conditions = df[['temp_label', 'voltage_label', 'current_label', 
                           'usage_label', 'fan_label']].sum(axis=1)
    df.loc[warning_conditions >= 1, 'cpu_state'] = 1
    df.loc[warning_conditions >= 2, 'cpu_state'] = 2
    
    return df

def main():
    # Create data directory if it doesn't exist
    # os.makedirs('../../data', exist_ok=True)
    
    # Generate data
    print("Generating synthetic data...")
    df = generate_synthetic_data()
    
    # Split into training and test sets (70:30)
    train_df, test_df = train_test_split(df, test_size=0.3, random_state=42)
    
    # Save datasets
    print("Saving datasets...")
    train_df.to_csv('data/train_data.csv', index=False)
    test_df.to_csv('data/test_data.csv', index=False)
    print("Data generation complete!")
    
    # Print some statistics
    print("\nDataset Statistics:")
    print(f"Total samples: {len(df)}")
    print(f"Training samples: {len(train_df)}")
    print(f"Test samples: {len(test_df)}")
    print("\nCPU State Distribution:")
    print(df['cpu_state'].value_counts().sort_index())

if __name__ == "__main__":
    main()
