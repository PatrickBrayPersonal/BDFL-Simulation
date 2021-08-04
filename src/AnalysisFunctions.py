import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import fnmatch
import os
 
class AnalysisFunctions:
    def __init__(self, filepath):
        self.filepath = filepath

    def gb_report(self, df, cols, by, plot_label, order_by=None, is_time_delta=True, show_graphs=True):
        '''
        Performs a groupby on df by "by" and returns a set of metrics on each col in cols
        '''
        df = df.copy()
        for col in cols:
            # Generate Tables
            print(col)
            if is_time_delta:
                df[col] = df[col].astype('timedelta64[D]')
            # Generate Metrics
            out_df = self.gb_metrics(df, by, col)
            # optional to reorder the groups
            if order_by:
                out_df = out_df.sort_values(order_by)
            self.to_excel(out_df, col + '_by_' + plot_label)
            # Create box and whisker plot
            if show_graphs:
                self.gb_boxplot(out_df, df, col, by, plot_label)
            return out_df

    def gb_boxplot(self, out_df, df, col, by, plot_label):
        '''
        intended to be called by gb_report
        creates a boxplot based on a groupby "by" for the column "col"
        '''
        # Plot Data
        fig1, ax1 = plt.subplots()
        ax1.set_title(col + ' by ' + plot_label)
        ax1.set_xlabel(col)
        ax1.set_ylabel(plot_label)
        options = out_df.index
        ax1.set_yticklabels(options)
        ax1.legend(options)
        option_dfs = [df[df[by]==option][col] for option in options]
        ax1.boxplot(option_dfs, vert=False)

    def gb_metrics(self, df, by, col):
        '''
        intended to be called by gb_report
        returns a dataframe "out_df" with metrics based on df
        '''
        out_df = pd.DataFrame()
        out_df['MEAN'] = round(df.groupby(by)[col].mean(), 3)
        out_df['MEDIAN'] = df.groupby(by)[col].median()
        out_df['MAX'] = df.groupby(by)[col].max()
        out_df['MIN'] = df.groupby(by)[col].min()
        out_df['RANGE'] = out_df['MAX'] - out_df['MIN']
        out_df['MODE'] = df.groupby(by)[col].agg(lambda x: x.value_counts().index[0])
        out_df['COUNT'] = df.groupby(by)[col].count()
        out_df['STDEV'] = round(df.groupby(by)[col].std(), 3)
        return out_df

    def to_excel(self, df, filename, has_date=False, has_time=False, output_path='/outputs/', index=False):
        '''
        standardized method for writing and labelling excel files from pandas dataframes
        has_date - will include date in filename
        has_time - will include time in filename
        output_path - defaults to 'outputs/' can be changed to write elsewhere
        '''
        # current date and time
        now = datetime.now()
        if has_date:
            filename = filename + now.strftime(' %m-%d-%Y')
        if has_time:
            filename = filename + now.strftime(' %H%M%S')
        df.to_excel(self.filepath + output_path + filename + '.xlsx', index=index)

    def most_recent_file(self, pattern=None, data_folder='/data'):
        '''
        returns the filepath of the most recently modified filewithin the data_folder specified
        you can filter the options by passing a regex string into pattern
        '''
        max_mtime = 0
        for dirname,subdirs,files in os.walk(self.filepath + data_folder):
            if pattern:
                files = fnmatch.filter(files, pattern)
            for fname in files:
                full_path = os.path.join(dirname, fname)
                mtime = os.stat(full_path).st_mtime
                if mtime > max_mtime:
                    max_mtime = mtime
                    max_dir = dirname
                    max_file = fname
        print('Most recent file is :', max_file)
        return max_dir + '/' + max_file
    
    
    def invert_dict(self, my_map):
        '''
        returns dictionary my_map inverted
        '''
        return {v: k for k, v in my_map.items()}
        