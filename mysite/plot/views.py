from django.http import HttpResponse
from django.template import loader
from datetime import datetime
from plotly.offline import plot
from plotly.graph_objs import Bar,Layout

from .models import Shareholder, Participant

import pandas as pd
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def get_browser():
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	br = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)
	return br

def index(request):

	shareholder_list = []
	participant_list = []
	start_date = 'YYYY/mm/dd'
	end_date = 'YYYY/mm/dd'
	stock = ''
	start_date2 = 'YYYY/mm/dd'
	end_date2 = 'YYYY/mm/dd'
	stock2 = ''
	threshold2 = ''
	plot_div = None

	if request.method == 'POST' and 'OK1' in request.POST:
		start_date = request.POST['start_date']
		end_date = request.POST['end_date']
		stock = request.POST['stock']

		URL = "https://www.hkexnews.hk/sdw/search/searchsdw.aspx"
		browser = get_browser()
		browser.get(URL)

		js = """document.getElementById('txtShareholdingDate').value='{}';
		document.getElementById('txtStockCode').value='{}';""".format(
		    end_date,stock
		)
		browser.execute_script(js)
		browser.find_element(By.ID, "txtShareholdingDate").click()
		browser.find_element(By.ID, "btnSearch").click()

		soup = BeautifulSoup(browser.page_source, "html.parser")
		browser.close()
		browser.quit()

		all_tables=[[td.text for td in tr.find_all('td')] for tr in soup.find_all('table')[0].find_all('tr')]
		part_info=[[sub_item.replace('\n', '') for sub_item in item] for item in all_tables[1:]]
		part_info = [dict(x.split(":") for x in item) for item in part_info]

		df = pd.DataFrame(part_info)
		df = df.rename(columns = {list(df)[0]:'pid', 
			                     list(df)[1]:'name', 
			                     list(df)[2]:'address', 
			                     list(df)[3]:'share', 
			                     list(df)[4]:'percent'})
		df.share = df.share.apply(lambda x: int(x.replace(',', '')))
		df.percent = df.percent.apply(lambda x: float(x.replace('%', '')))
		Shareholder.objects.all().delete()
		for index, row in df.iterrows():
			q = Shareholder(pid=row['pid'], name=row['name'], address=row['address'], share=row['share'], percent=row['percent'])
			q.save()
		shareholder_list = Shareholder.objects.order_by('-share')
		plot_list = Shareholder.objects.order_by('-share')[:10]
		x = [i.pid for i in plot_list]
		y = [i.share for i in plot_list]
		plot_div = plot({'data':[Bar(x=x, y=y, name='plot')], "layout": Layout(title="Shareholding of the top 10 participant as of the end date", xaxis=dict(title='Participant ID'), yaxis=dict(title='Shareholding'))},output_type='div')


	elif request.method == 'POST' and 'OK2' in request.POST:
		start_date2 = request.POST['start_date2']
		end_date2 = request.POST['end_date2']
		stock2 = request.POST['stock2']
		threshold2 = float(request.POST['threshold2'])

		URL = "https://www.hkexnews.hk/sdw/search/searchsdw.aspx"
		browser = get_browser()
		browser.get(URL)

		st = datetime.strptime(start_date2, "%Y/%m/%d").date()
		ed = datetime.strptime(end_date2, "%Y/%m/%d").date()

		date_list = pd.date_range(
			start=st, end=ed, freq="1D"
		).strftime("%Y/%m/%d")

		df_all = []
		df_pre = pd.DataFrame()
		for date in date_list:
			js = """document.getElementById('txtShareholdingDate').value='{}';
			document.getElementById('txtStockCode').value='{}';""".format(
			    date,stock2
			)
			browser.execute_script(js)
			browser.find_element(By.ID, "txtShareholdingDate").click()
			browser.find_element(By.ID, "btnSearch").click()

			soup = BeautifulSoup(browser.page_source, "html.parser")
			all_tables=[[td.text for td in tr.find_all('td')] for tr in soup.find_all('table')[0].find_all('tr')]
			part_info=[[sub_item.replace('\n', '') for sub_item in item] for item in all_tables[1:]]
			part_info = [dict(x.split(":") for x in item) for item in part_info]

			df = pd.DataFrame(part_info)
			df = df.rename(columns = {list(df)[0]:'pid', 
			                     list(df)[1]:'name', 
			                     list(df)[2]:'address', 
			                     list(df)[3]:'share', 
			                     list(df)[4]:'percent'})
			df.share = df.share.apply(lambda x: int(x.replace(',', '')))
			df.percent = df.percent.apply(lambda x: float(x.replace('%', '')))
			if len(df_pre) > 0 and len(df) > 0:
				re = df_pre.merge(df, on = ['pid'])
				re = re.loc[(re.percent_x - re.percent_y).abs() >= threshold2]
				if len(re) > 1:
					df_all.append({'date':date, 'pid': ', '.join(re.pid.values), 'name': ', '.join(re.name_x.values)})
			df_pre = df
		df_all = pd.DataFrame(df_all)
		Participant.objects.all().delete()
		for index, row in df_all.iterrows():
			q = Participant(date = row['date'], pid=row['pid'], name=row['name'])
			q.save()

		participant_list = Participant.objects.order_by('-date')

		browser.close()
		browser.quit()



	template = loader.get_template('plot/index.html')
	context = {
		'shareholder_list': shareholder_list,
		'participant_list': participant_list, 
		'start_date': start_date,
		'end_date': end_date,
		'stock': stock,
		'start_date2': start_date2,
		'end_date2': end_date2,
		'stock2': stock2,
		'threshold2': threshold2,
                'plot_div': plot_div
	}
	return HttpResponse(template.render(context, request))
