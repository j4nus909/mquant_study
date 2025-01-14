import ast
import requests
from datetime import date, timedelta

class Krx:

    isin_code = 'KR7005930003'
    start_date = '2019/04/20'
    end_date = '2019/06/20'

    def main(self):

        start = date(int(self.start_date.split("/")[0]), int(self.start_date.split("/")[1]), int(self.start_date.split("/")[2]))
        end = date(int(self.end_date.split("/")[0]), int(self.end_date.split("/")[1]), int(self.end_date.split("/")[2]))

        delta = end - start

        day_price_data = self.get_day_price()
        short_stock_selling_data = self.get_short_stock_selling()
        kospi_index_data = self.get_kospi_kosdaq_index('kospi')
        kosdaq_index_data = self.get_kospi_kosdaq_index('kosdaq')

        print("년/월/일|종가|시가|고가|저가|거래대금|공매도거래대금|공매도잔고금액|기관거래대금순매수|외국인거래대금순매수|코스피종가|코스닥종가")

        for day in range(delta.days+1):
            d = start + timedelta(days=day)
            key = str(d).replace("-", "")

            if key in day_price_data:

                amounts = self.get_org_alien_amounts(key)

                print(str(d).replace("-", "/") + "|" + day_price_data[key][0] + "|" + day_price_data[key][1] + "|" + day_price_data[key][2] + "|" + day_price_data[key][3] + "|" + day_price_data[key][4]
                      + "|" + short_stock_selling_data[key][2] + "|" + short_stock_selling_data[key][3]
                      + "|" + amounts['기관합계'] + "|" + amounts['외국인']
                      + "|" + kospi_index_data[key] + "|" + kosdaq_index_data[key])

    def get_day_price(self):

        #krx menu 30040 일자별 시세

        otp = requests.get('http://marketdata.krx.co.kr/contents/COM/GenerateOTP.jspx?bld=MKD/04/0402/04020100/mkd04020100t3_02&name=chart')

        parameters = {
            'isu_cd': self.isin_code,
            'fromdate': self.start_date.replace("/", ""),
            'todate': self.end_date.replace("/", ""),
            'pagePath': '/contents/MKD/04/0402/04020100/MKD04020100T3T2.jsp',
            'code': otp.content
        }

        res = requests.post('http://marketdata.krx.co.kr/contents/MKD/99/MKD99000001.jspx', parameters)

        data = ast.literal_eval(res.text)['block1']

        result = {}

        for item in data:
            # tdd_clsprc : 종가
            # acc_trdval : 거래대금
            # tdd_opnprc : 시가
            # tdd_hgprc : 고가
            # tdd_lwprc : 저가
            result[item['trd_dd'].replace("/", "")] = (item['tdd_clsprc'], item['tdd_opnprc'], item['tdd_hgprc'], item['tdd_lwprc'], item['acc_trdval'])

        return result

    def get_short_stock_selling(self):

        # reverse engineered from the source at here https://finance.naver.com/item/short_trade.nhn?code=005930
        otp = requests.get('https://short.krx.co.kr/contents/COM/GenerateOTP.jspx?bld=SRT/02/02010100/srt02010100X&name=form')

        parameters = {
            'isu_cd': self.isin_code,
            'strt_dd': self.start_date.replace("/", ""),
            'end_dd': self.end_date.replace("/", ""),
            'pagePath': '/contents/SRT/02/02010100/SRT02010100X.jsp',
            'code': otp.content
        }

        res = requests.post('https://short.krx.co.kr/contents/SRT/99/SRT99000001.jspx', parameters)

        data = ast.literal_eval(res.text)['block1']

        result = {}

        for item in data:
            # cvsrtsell_trdvol : 공매도 거래량
            # str_const_val1 : 공매도 잔고량
            # cvsrtsell_trdval : 공매도 거래대금
            # str_const_val2 : 공매도 잔고금액
            result[item['trd_dd'].replace("/", "")] = (item['cvsrtsell_trdvol'], item['str_const_val1'], item['cvsrtsell_trdval'], item['str_const_val2'])

        return result

    def get_kospi_kosdaq_index(self, index_type):

        # krx menu 80001 개별지수 추이

        type = None
        ind_type = None

        if index_type == "kospi":
            type = "3"
            ind_type = "1001"
        elif index_type == "kosdaq":
            type = "4"
            ind_type = "2001"

        otp = requests.get('http://marketdata.krx.co.kr/contents/COM/GenerateOTP.jspx?bld=MKD/13/1301/13010102/mkd13010102&name=form')

        parameters = {
            'type': type,
            'ind_type': ind_type,
            'period_strt_dd': self.start_date.replace("/", ""),
            'period_end_dd': self.end_date.replace("/", ""),
            'pagePath': '/contents/MKD/13/1301/13010102/MKD13010102.jsp',
            'code': otp.content
        }

        res = requests.post('http://marketdata.krx.co.kr/contents/MKD/99/MKD99000001.jspx', parameters)

        data = ast.literal_eval(res.text)['block1']

        result = {}

        for item in data:
            #indx : 종가
            result[item['work_dt'].replace("/", "")] = item['indx']

        return result

    def get_org_alien_amounts(self, date):

        # krx menu 80019 투자자별거래실적 (개별종목)

        otp = requests.get('http://marketdata.krx.co.kr/contents/COM/GenerateOTP.jspx?bld=MKD/13/1302/13020303/mkd13020303&name=form')

        parameters = {
            'isu_cd': self.isin_code,
            'period_selector':'day',
            'fromdate': date,
            'todate': date,
            'pagePath': '/contents/MKD/13/1302/13020303/MKD13020303.jsp',
            'code': otp.content
        }

        res = requests.post('http://marketdata.krx.co.kr/contents/MKD/99/MKD99000001.jspx', parameters)

        data = ast.literal_eval(res.text)['block1']

        result = {}

        for item in data:
            # netaskval : 거래대금(원) 순매수
            if item['invst_nm'] == '기관합계' or item['invst_nm'] == '외국인':
                result[item['invst_nm']] = item['netaskval']

        return result

if __name__ == "__main__":
    Krx().main()

