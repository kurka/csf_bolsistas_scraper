import scrapy
from bs4 import BeautifulSoup


class CSFSpider(scrapy.Spider):
    name = "csf_universities"
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

            # yield uni_info
            yield uni_info

