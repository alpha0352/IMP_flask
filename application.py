from flask import Flask, request, render_template, session, redirect,url_for,send_file,jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import plotly.express as px
from plotly import utils
import json

fig,ax = plt.subplots(figsize = (6,6))

app = Flask(__name__)
app.secret_key = "Alpha352"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://root:Alpha0352@localhost/invest_portfolio'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)
# class Transactions(db.Model):
       
#     Tid = db.Column(db.String(15),primary_key = True)
#     Tdate = db.Column(db.Date)
#     Scrip = db.Column(db.String(10),primary_key = True)
#     Volume = db.Column(db.Integer)
#     Rate = db.Column(db.Double)
#     Debit = db.Column(db.Double)
#     Credit = db.Column(db.Double)
#     Balance = db.Column(db.Double)

#     def __init__(self,tid,tdate,scrip,volume,rate,debit,credit,balance):
#          self.Tid = tid
#          self.Tdate = tdate
#          self.Scrip = scrip
#          self.Volume = volume
#          self.Rate = rate
#          self.Debit = debit
#          self.Credit = credit
#          self.Balance = balance
     
#     def __init__(self, tid=None, tdate=None, scrip=None, volume=None, rate=None, debit=None, credit=None, balance=None):
#          self.Tid = tid
#          self.Tdate = tdate
#          self.Scrip = scrip
#          self.Volume = volume
#          self.Rate = rate
#          self.Debit = debit
#          self.Credit = credit
#          self.Balance = balance

@app.route('/',methods=(["GET"]))
def home_page():
    # TData = Transactions()
    # allData = TData.query.all()

    portfolio = []
    current_holding_sums = {}
    # data = pd.read_sql_table('transactions', db.get_engine().connect())
    data = pd.read_csv('./data/processed_data.csv')
    # data = pd.DataFrame([{
    #     'TDate': txn.Tdate,
    #     'Scrip': txn.Scrip,
    #     'volume': txn.Volume,
    #     'debit': txn.Debit,
    #     'credit': txn.Credit
    # } for txn in allData])

    data['volume'] = data['volume'].astype(int)
    data['TDate'] = pd.to_datetime(data['TDate'],dayfirst=True)
    data['debit'] = data['debit'].astype(float)
    data['credit'] = data['credit'].astype(float)

    for scrip_name in data['Scrip'].unique():
        filtered_data = data[(data['TDate'].dt.year >= 2022) & (data['Scrip'] == scrip_name)]
        buy_volume = filtered_data.loc[filtered_data['debit'] != 0, 'volume'].sum()
        sell_volume = filtered_data.loc[filtered_data['credit'] != 0, 'volume'].sum()
        # bonus_volume = filtered_bondiv['Bonus Share'].sum()
        # dividend = filtered_bondiv['Dividend'].sum()
        # Current_Holding = buy_volume - sell_volume + bonus_volume
        current_holding = buy_volume - sell_volume

        if current_holding > 0:
            buy_avg= (filtered_data['debit'].sum() - filtered_data['credit'].sum() ) / (current_holding)
            Buy_avg_divin= (filtered_data['debit'].sum() - filtered_data['credit'].sum()) / (current_holding)
            portfolio.append({'scrip':scrip_name,
                              'buy_vol':buy_volume,
                              'sell_vol':sell_volume,
                              'curr_vol':round(current_holding,2),
                              'buy_avg':round(buy_avg,2)})
            current_holding_sums[scrip_name] = current_holding

        #plotting pie chart
        labels = list(current_holding_sums.keys())
        values = list(current_holding_sums.values())
        fig = px.pie(data, values=values, names=labels)
        fig.update_layout(
                width = 550,
                height = 455,
                plot_bgcolor = ' rgba(255,255,255,0.85)',
                paper_bgcolor = 'rgba(255,255,255,0.85)',
                legend = dict(bgcolor = 'white'),
                font_color= '#333333'
                )
        plotly_plot = json.dumps(fig, cls=utils.PlotlyJSONEncoder)
        # print(portfolio)
    return render_template('home.html',portfolio=portfolio,plotly_plot=plotly_plot)

@app.route('/transactions',methods=(["GET"]))
def transactions_page():
    TData = Transactions()
    allData = TData.query.all()
    for data in allData:
        print(data.Tid)
        print(data.Tdate)
        print("--------------------")
    return render_template('transactions.html',allData=allData)

@app.route('/watchlist',methods=(["GET"]))
def watchlist_page():
     return render_template('watchlist.html')

@app.route('/insert')
def insert_page():
    return render_template('forms.html')

@app.route('/insert_form',methods =["POST"])
def insert_form():
     
    tid = request.form['tid']
    tdate = request.form['tdate']
    scrip =request.form['scrip']
    volume =request.form['volume'] 
    rate = request.form['rate']
    debit = request.form['debit']
    credit =request.form['credit'] 
    balance = request.form['balance']
    print(tid,tdate,scrip,volume,rate,debit,credit,balance) 
    insert_data = Transactions(tid,tdate,scrip,volume,rate,debit,credit,balance)

    db.session.add(insert_data)
    db.session.commit()

    return redirect(url_for('Index'))

@app.route('/holdings_graph',methods = ["GET"])
def holdings_graph():
    data = pd.read_sql_table('transactions', db.get_engine().connect())
    unique_values = data['Scrip'].unique()
    current_holding_sums = {}
    print(unique_values)
    for value in unique_values:
        temp = data[data['Scrip'] == value]
        # print(temp)
        buy_volume = temp.loc[temp['debit'] != 0, 'volume'].sum()
        sell_volume = temp.loc[temp['credit'] != 0, 'volume'].sum()
        # bonus_volume = filtered_bondiv['Bonus Share'].sum()
        current_holding = buy_volume - sell_volume #+ bonus_volume
        if current_holding > 0:
            current_holding_sums[value] = current_holding
            
    # Plotting the pie chart
    labels = list(current_holding_sums.keys())
    values = list(current_holding_sums.values())

    plt.title('Current Holdings')
    plt.pie(values,radius=1,autopct='%1.1f%%',startangle = 65)

    centre_circle = plt.Circle((0,0),0.8,fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
   
    plt.legend(labels,ncols = 4,bbox_to_anchor=(0.5,-0.1),loc = 'upper center')
    
    ax.axis('equal')  
    plt.tight_layout()

    canvas = FigureCanvas(fig)
    img = io.BytesIO()
    fig.savefig(img)
    img.seek(0)
    return send_file(img,mimetype = 'img/png')
    # plt.show()

if __name__== "__main__":
    app.run(debug=True)


