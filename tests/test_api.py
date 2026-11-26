"""Testes de integração em SQLite isolado; não alteram o banco da equipe."""
import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

_tmp = tempfile.TemporaryDirectory()
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(_tmp.name) / 'teste.db')
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy.orm import close_all_sessions
from app.database import SessionLocal, engine
from app.models import Cliente, Categoria, Veiculo, Acessorio
from decimal import Decimal


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        command.upgrade(Config('alembic.ini'), 'head')
        with SessionLocal() as db:
            c = Categoria(nome='Teste', valor_diaria=Decimal('100'))
            db.add_all([c, Cliente(nome='Teste', cpf='12345678909', cnh='12345678901', email='teste@example.com', telefone='123456789', ativo=True), Acessorio(nome='GPS', valor_diaria=Decimal('20'))])
            db.flush()
            for i in range(1, 8):
                db.add(Veiculo(placa=f'TST{i:04}', marca='Teste', modelo='Teste', ano=2024, categoria_id=c.id, quilometragem=100))
            db.commit()
        cls.api = TestClient(app)
        cls.hoje = date.today()

    def d(self, offset):
        return (self.hoje + timedelta(days=offset)).isoformat()

    def req(self, method, path, code, **kw):
        r = self.api.request(method, path, **kw)
        self.assertEqual(r.status_code, code, r.text)
        return r.json() if r.content else None

    def reservar(self, v, inicio, fim, code=201, extras=()):
        return self.req('POST', '/locacoes', code, json={'cliente_id':1,'veiculo_id':v,'data_inicio':self.d(inicio),'data_fim':self.d(fim),'acessorios_ids':list(extras)})

    def test_conflitos_e_manutencao(self):
        a = self.reservar(1, 10, 15, extras=[1])
        self.assertEqual(Decimal(a['valor_total']), 600)
        self.reservar(1, 12, 14, 409)
        self.reservar(1, 15, 18)
        self.req('POST','/manutencoes',409,json={'veiculo_id':1,'descricao':'Revisão','data_inicio':self.d(11),'data_fim':self.d(13)})
        m = self.req('POST','/manutencoes',201,json={'veiculo_id':1,'descricao':'Revisão','data_inicio':self.d(20),'data_fim':self.d(25)})
        self.reservar(1, 21, 23, 409)
        self.req('PUT',f"/locacoes/{a['id']}",409,json={'data_inicio':self.d(21),'data_fim':self.d(23)})
        self.req('PUT',f"/manutencoes/{m['id']}",422,json={'data_fim':self.d(19)})
        livres = self.req('GET','/veiculos/disponiveis',200,params={'data_inicio':self.d(21),'data_fim':self.d(23)})
        self.assertNotIn(1,[x['id'] for x in livres])
        self.req('PUT',f"/locacoes/{a['id']}",200,json={'status':'cancelada'})
        self.reservar(1,10,15)
        self.req('PUT',f"/locacoes/{a['id']}",409,json={'status':'ativa'})

    def test_retirada_devolucao(self):
        a = self.reservar(2,0,2,extras=[1]); path=f"/locacoes/{a['id']}"
        self.req('PUT',path,200,json={'status':'ativa','quilometragem_retirada':110,'condicao_retirada':'Boa'})
        self.req('PUT',path,422,json={'status':'finalizada','quilometragem_devolucao':100})
        b=self.req('PUT',path,200,json={'status':'finalizada','quilometragem_devolucao':150,'condicao_devolucao':'Boa'})
        self.assertEqual(b['quilometragem_devolucao'],150)
        self.assertEqual(self.req('GET','/veiculos/2',200)['quilometragem'],150)
        self.req('POST','/pagamentos',201,json={'locacao_id':a['id'],'valor':240,'forma':'pix','status':'pago'})
        self.req('GET','/veiculos/2/locacoes',200)

    def test_atraso(self):
        from app.models import Locacao
        from app.models.enums import StatusLocacao, StatusVeiculo
        a=self.reservar(3,-5,-2); b=self.reservar(3,-2,2)
        with SessionLocal() as db:
            loc=db.get(Locacao,a['id']); loc.status=StatusLocacao.ATIVA; loc.veiculo.status=StatusVeiculo.ALUGADO; db.commit()
        self.reservar(3,5,7,409)
        self.assertIn(a['id'],[x['id'] for x in self.req('GET','/locacoes/atrasadas',200)])
        self.req('PUT',f"/locacoes/{a['id']}",200,json={'status':'finalizada'})
        self.assertEqual(self.req('GET',f"/locacoes/{b['id']}",200)['status'],'cancelada')
        self.reservar(3,5,7)

    def test_consultas(self):
        for path in ['/saude','/categorias','/clientes/','/veiculos/','/locacoes','/pagamentos','/manutencoes','/acessorios','/estatisticas','/consultas/veiculos/nunca-locados','/consultas/veiculos/manutencao-e-locacao-futura','/clientes/1/locacoes']:
            self.req('GET',path,200)
        self.req('GET','/estatisticas/utilizacao-frota',200,params={'data_inicio':self.d(-10),'data_fim':self.d(1)})
        self.req('GET','/consultas/clientes/1/locacoes',200,params={'data_inicio':self.d(-10),'data_fim':self.d(10)})
        self.req('GET','/locacoes?limit=-1',422)
        self.req('GET','/veiculos/9999',404)
        self.reservar(7,5,3,422)

    @classmethod
    def tearDownClass(cls):
        cls.api.close()
        close_all_sessions()
        engine.dispose()
        _tmp.cleanup()

if __name__ == '__main__':
    unittest.main()
