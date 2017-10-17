import scrapy
import re
from bs4 import BeautifulSoup
from datetime import datetime, date


class CSFSpider(scrapy.Spider):
    name = "csf"
    start_urls = ["http://www.cienciasemfronteiras.gov.br/web/csf/bolsistas-pelo-mundo?p_p_id=mapabolsistasportlet_WAR_mapabolsistasportlet_INSTANCE_Y7eO&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&p_p_col_id=column-2&p_p_col_count=1&siglaPais=GBR&nomePais=Reino%20Unido&codigoArea=&tituloArea=Todas&siglaModalidade=&nomeModalidade=Todas#"]
    # start_urls = ["http://www.cienciasemfronteiras.gov.br/web/csf/bolsistas-pelo-mundo"]

    def parse(self, response):
        # Get from javascript code html fragments for each university (ugly, but works!)
        universities_pages = response.xpath('//*[@id="p_p_id_mapabolsistasportlet_WAR_mapabolsistasportlet_INSTANCE_Y7eO_"]/div/div/script[2]/text()').re(r's.setContent\("(<div class=\'infoMapa\'>.*?Todos os Bolsistas</a></ul></div>)"\);')

        # For each html fragment, corresponding to a university in uk...
        for uni in universities_pages:
            # Render the html string
            soup = BeautifulSoup(uni, 'lxml')

            # Store the individual counts, for scholarship types, in a dict
            count_modalidade = {
                m.text[:-1]: c.text
                for (m, c) in zip(soup.find_all(class_="modalidade"),
                                  soup.find_all(class_="numModal"))
            }

            # Store general information for the university
            uni_info = {
                'university_name': soup.h3.text,
                'university_website': soup.a.get("href"),
                'university_address': soup.li.text,
                'modalidades_count': count_modalidade,
            }

            id_uni = re.match(r'mostraBolsas\(\\"(.*?)\\",',
                              soup.find(class_="botaoLinkA")["onclick"]).group(1)

            # build link with all students information
            all_students_base_url ="http://www.cienciasemfronteiras.gov.br/web/csf/bolsistas-pelo-mundo?p_p_id=mapabolsistasportlet_WAR_mapabolsistasportlet_INSTANCE_Y7eO&p_p_lifecycle=0&p_p_state=pop_up&p_p_mode=help&p_p_col_id=column-2&p_p_col_count=1&modal=modal&idDest="
            uni_students_url = all_students_base_url + id_uni

            # yield uni_info as independent object
            yield uni_info

            #follow the link to get students info
            request = scrapy.Request(uni_students_url,
                                     callback=self.parse_students)
            #send uni_info to parse_students parser
            request.meta["uni_info"] = uni_info
            yield request


    def parse_students(self, response):
        uni_info = response.meta["uni_info"]
        uni_name = uni_info["university_name"]

        soup = BeautifulSoup(response.text, 'lxml')
        for st in soup.find_all(class_="corpoBolsas"):
            univ_categ_re = re.search(r"(.*) (Bolsista .*)", st.contents[2])
            univ_lattes = univ_categ_re.group(1).strip()
            categ = univ_categ_re.group(2).strip()
            vigencia_start, vigencia_end = map(lambda s: datetime.strptime(s, "%d/%m/%Y").date(),
                                               st.contents[-1].strip().split(" a "))
            student_info = {
                'student_name': st.h2.text.strip(),
                'email_lattes': st.find(title="Enviar Email")["href"],
                'cv_lattes': st.find(title=re.compile("Visualizar Curr.culo"))["href"],
                'univ_csf': uni_name,
                'univ_lattes': univ_lattes, # TODO: split city
                'bolsista_type': categ,
                'area_prioritaria': st.contents[6].strip(),  # FIXME: dangerous index!
                'area_conhecimento': st.contents[8].strip(),  # FIXME: dangerous index!
                'vigencia_start': vigencia_start.isoformat(),
                'vigencia_end': vigencia_end.isoformat(),
                'vigente': vigencia_end > date.today()
            }

            yield student_info
