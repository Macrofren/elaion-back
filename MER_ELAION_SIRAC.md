<!--

erDiagram
    direction LR
usuario {
 BIGINT id PK
   BOOLEAN ativo 
   VARCHAR(14) cpf 
   DATETIME criado_em 
   VARCHAR(100) email 
   VARCHAR(50) login 
   VARCHAR(150) nome_completo 
   VARCHAR(8) papel 
   VARCHAR(255) senha_hash 
   VARCHAR(20) telefone 
   VARCHAR(30) turno 
}
terminal {
 BIGINT id PK
   BOOLEAN ativo 
   VARCHAR(50) codigo 
   DATETIME criado_em 
   VARCHAR(100) nome 
}
laboratorio {
 BIGINT id PK
   BOOLEAN ativo 
   VARCHAR(50) codigo 
   DATETIME criado_em 
   VARCHAR(100) nome 
   BIGINT terminal_id 
}
tanque {
 BIGINT id PK
   BOOLEAN ativo 
   NUMERIC(12,_2) capacidade_litros 
   DATETIME criado_em 
   VARCHAR(50) identificador_tanque 
   BIGINT produto_id 
   BIGINT terminal_id 
}
congenere {
 BIGINT id PK
   VARCHAR(50) codigo_sicof 
   DATETIME criado_em 
   VARCHAR(100) nome 
}
transportadora {
 BIGINT id PK
   DATETIME criado_em 
   BOOLEAN is_propria 
   VARCHAR(150) nome 
}
produto {
 BIGINT id PK
   VARCHAR(50) categoria 
   DATETIME criado_em 
   VARCHAR(100) nome 
   VARCHAR(20) unidade_medida 
}
veiculo_produto {
 BIGINT id PK
   BIGINT produto_id 
   BIGINT veiculo_id 
}
veiculo {
 BIGINT id PK
   NUMERIC(12,_2) capacidade_total_litros 
   BIGINT congenere_id 
   DATETIME data_hora_entrada 
   DATETIME data_hora_saida 
   BOOLEAN is_transportadora_propria 
   VARCHAR(255) motivo_cancelamento 
   VARCHAR(150) nome_motorista 
   INTEGER numero_compartimentos 
   VARCHAR(50) numero_nota_fiscal 
   TEXT observacao_cancelamento 
   TEXT observacao_geral 
   VARCHAR(150) origem 
   VARCHAR(10) placa 
   VARCHAR(10) status_portaria 
   BIGINT terminal_id 
   BIGINT transportadora_id 
   BIGINT usuario_aprovacao_saida_id 
   BIGINT usuario_registro_id 
   NUMERIC(12,_2) volume_nota_fiscal_litros 
}
coleta_amostra {
 BIGINT id PK
   BIGINT amostrador_id 
   DATETIME data_hora_coleta 
   INTEGER numero_coleta 
   VARCHAR(30) status 
   BIGINT usuario_recebimento_id 
   BIGINT veiculo_id 
}
amostra {
 BIGINT id PK
   NUMERIC(12,_2) capacidade_compartimento_litros 
   VARCHAR(30) codigo_amostra 
   BIGINT coleta_id 
   DATETIME data_hora_coleta 
   DATETIME data_hora_fim_analise 
   DATETIME data_hora_recoleta 
   DATETIME data_hora_reprovacao 
   VARCHAR(10) etapa_analise 
   VARCHAR(10) identificador_compartimento 
   BOOLEAN is_recoleta 
   TEXT motivo_recoleta 
   TEXT motivo_reprovacao 
   BIGINT operador_id 
   VARCHAR(30) origem_procedimento 
   BIGINT produto_id 
   VARCHAR(9) status_resultado 
   NUMERIC(5,_2) temperatura_coleta_celsius 
   BIGINT usuario_recoleta_id 
   BIGINT usuario_reprovacao_id 
   BIGINT veiculo_id 
}
analise_amostra {
 BIGINT id PK
   BOOLEAN agua_livre 
   BIGINT amostra_id 
   BIGINT analista_id 
   VARCHAR(50) aspecto 
   VARCHAR(50) cor 
   DATETIME data_hora_analise 
   NUMERIC(8,_4) densidade_kg_l 
   NUMERIC(6,_4) fator_correcao 
   NUMERIC(5,_2) grau_inpm 
   BIGINT laboratorio_id 
   NUMERIC(8,_4) massa_especifica_20c_kg_l 
   BOOLEAN material_particulado 
   VARCHAR(30) numero_amostra_lab 
   TEXT observacoes 
   NUMERIC(5,_2) temperatura_ensaio_celsius 
   NUMERIC(8,_2) teor_agua_ppm 
   VARCHAR(50) tipo_especifico_produto 
   VARCHAR(50) visto_analista 
}
comprovante_amostra {
 BIGINT id PK
   TEXT complemento_observacoes 
   BIGINT congenere_id 
   BIGINT criado_por_usuario_id 
   DATE data_geracao 
   NUMERIC(8,_4) densidade_20c_apurada 
   NUMERIC(6,_4) fator_correcao 
   NUMERIC(5,_2) grau_inpm 
   TIME hora_geracao 
   VARCHAR(50) lancamento_sicof 
   VARCHAR(50) nota_fiscal_numero 
   VARCHAR(50) numero_sicof 
   NUMERIC(12,_2) resultado_variacao_litros 
   VARCHAR(10) status 
   BIGINT tanque_descarga_id 
   BIGINT veiculo_id 
   NUMERIC(12,_2) volume_20c_apurado_litros 
   NUMERIC(12,_2) volume_20c_nf_litros 
   NUMERIC(12,_2) volume_ambiente_apurado_litros 
   NUMERIC(12,_2) volume_ambiente_nf_litros 
   NUMERIC(12,_2) volume_retirada_litros 
}
comprovante_amostra_item {
 BIGINT id PK
   BIGINT amostra_id 
   BIGINT comprovante_id 
}
historico_edicao_comprovante {
 BIGINT id PK
   BIGINT comprovante_id 
   DATETIME data_hora 
   TEXT descricao_acao 
   BIGINT usuario_id 
}
historico_edicao_veiculo {
 BIGINT id PK
   VARCHAR(100) campo_alterado 
   DATETIME data_hora 
   TEXT motivo 
   BIGINT usuario_id 
   TEXT valor_anterior 
   TEXT valor_novo 
   BIGINT veiculo_id 
}
historico_edicao_amostra {
 BIGINT id PK
   BIGINT amostra_id 
   VARCHAR(100) campo_alterado 
   DATETIME data_hora 
   TEXT motivo 
   BIGINT usuario_id 
   TEXT valor_anterior 
   TEXT valor_novo 
}
historico_edicao_analise {
 BIGINT id PK
   BIGINT analise_amostra_id 
   VARCHAR(100) campo_alterado 
   DATETIME data_hora 
   TEXT motivo 
   BIGINT usuario_id 
   TEXT valor_anterior 
   TEXT valor_novo 
}
terminal 1--0+ laboratorio : has
terminal 1--0+ tanque : has
produto 1--0+ tanque : has
produto 1--0+ veiculo_produto : has
veiculo 1--0+ veiculo_produto : has
congenere 1--0+ veiculo : has
usuario one or zero--0+ veiculo : has
transportadora 1--0+ veiculo : has
usuario 1--0+ veiculo : has
terminal 1--0+ veiculo : has
veiculo 1--0+ coleta_amostra : has
usuario one or zero--0+ coleta_amostra : has
usuario one or zero--0+ coleta_amostra : has
produto 1--0+ amostra : has
usuario one or zero--0+ amostra : has
coleta_amostra 1--0+ amostra : has
usuario one or zero--0+ amostra : has
usuario one or zero--0+ amostra : has
veiculo 1--0+ amostra : has
amostra 1--0+ analise_amostra : has
laboratorio one or zero--0+ analise_amostra : has
usuario 1--0+ analise_amostra : has
veiculo 1--0+ comprovante_amostra : has
congenere 1--0+ comprovante_amostra : has
usuario 1--0+ comprovante_amostra : has
tanque one or zero--0+ comprovante_amostra : has
amostra 1--0+ comprovante_amostra_item : has
comprovante_amostra 1--0+ comprovante_amostra_item : has
comprovante_amostra 1--0+ historico_edicao_comprovante : has
usuario 1--0+ historico_edicao_comprovante : has
veiculo 1--0+ historico_edicao_veiculo : has
usuario 1--0+ historico_edicao_veiculo : has
usuario 1--0+ historico_edicao_amostra : has
amostra 1--0+ historico_edicao_amostra : has
usuario 1--0+ historico_edicao_analise : has
analise_amostra 1--0+ historico_edicao_analise : has

-->
![](https://mermaid.ink/img/ZXJEaWFncmFtCnVzdWFyaW8gewogQklHSU5UIGlkIFBLCiAgIEJPT0xFQU4gYXRpdm8gCiAgIFZBUkNIQVIoMTQpIGNwZiAKICAgREFURVRJTUUgY3JpYWRvX2VtIAogICBWQVJDSEFSKDEwMCkgZW1haWwgCiAgIFZBUkNIQVIoNTApIGxvZ2luIAogICBWQVJDSEFSKDE1MCkgbm9tZV9jb21wbGV0byAKICAgVkFSQ0hBUig4KSBwYXBlbCAKICAgVkFSQ0hBUigyNTUpIHNlbmhhX2hhc2ggCiAgIFZBUkNIQVIoMjApIHRlbGVmb25lIAogICBWQVJDSEFSKDMwKSB0dXJubyAKfQp0ZXJtaW5hbCB7CiBCSUdJTlQgaWQgUEsKICAgQk9PTEVBTiBhdGl2byAKICAgVkFSQ0hBUig1MCkgY29kaWdvIAogICBEQVRFVElNRSBjcmlhZG9fZW0gCiAgIFZBUkNIQVIoMTAwKSBub21lIAp9CmxhYm9yYXRvcmlvIHsKIEJJR0lOVCBpZCBQSwogICBCT09MRUFOIGF0aXZvIAogICBWQVJDSEFSKDUwKSBjb2RpZ28gCiAgIERBVEVUSU1FIGNyaWFkb19lbSAKICAgVkFSQ0hBUigxMDApIG5vbWUgCiAgIEJJR0lOVCB0ZXJtaW5hbF9pZCAKfQp0YW5xdWUgewogQklHSU5UIGlkIFBLCiAgIEJPT0xFQU4gYXRpdm8gCiAgIE5VTUVSSUMoMTIsXzIpIGNhcGFjaWRhZGVfbGl0cm9zIAogICBEQVRFVElNRSBjcmlhZG9fZW0gCiAgIFZBUkNIQVIoNTApIGlkZW50aWZpY2Fkb3JfdGFucXVlIAogICBCSUdJTlQgcHJvZHV0b19pZCAKICAgQklHSU5UIHRlcm1pbmFsX2lkIAp9CmNvbmdlbmVyZSB7CiBCSUdJTlQgaWQgUEsKICAgVkFSQ0hBUig1MCkgY29kaWdvX3NpY29mIAogICBEQVRFVElNRSBjcmlhZG9fZW0gCiAgIFZBUkNIQVIoMTAwKSBub21lIAp9CnRyYW5zcG9ydGFkb3JhIHsKIEJJR0lOVCBpZCBQSwogICBEQVRFVElNRSBjcmlhZG9fZW0gCiAgIEJPT0xFQU4gaXNfcHJvcHJpYSAKICAgVkFSQ0hBUigxNTApIG5vbWUgCn0KcHJvZHV0byB7CiBCSUdJTlQgaWQgUEsKICAgVkFSQ0hBUig1MCkgY2F0ZWdvcmlhIAogICBEQVRFVElNRSBjcmlhZG9fZW0gCiAgIFZBUkNIQVIoMTAwKSBub21lIAogICBWQVJDSEFSKDIwKSB1bmlkYWRlX21lZGlkYSAKfQp2ZWljdWxvX3Byb2R1dG8gewogQklHSU5UIGlkIFBLCiAgIEJJR0lOVCBwcm9kdXRvX2lkIAogICBCSUdJTlQgdmVpY3Vsb19pZCAKfQp2ZWljdWxvIHsKIEJJR0lOVCBpZCBQSwogICBOVU1FUklDKDEyLF8yKSBjYXBhY2lkYWRlX3RvdGFsX2xpdHJvcyAKICAgQklHSU5UIGNvbmdlbmVyZV9pZCAKICAgREFURVRJTUUgZGF0YV9ob3JhX2VudHJhZGEgCiAgIERBVEVUSU1FIGRhdGFfaG9yYV9zYWlkYSAKICAgQk9PTEVBTiBpc190cmFuc3BvcnRhZG9yYV9wcm9wcmlhIAogICBWQVJDSEFSKDI1NSkgbW90aXZvX2NhbmNlbGFtZW50byAKICAgVkFSQ0hBUigxNTApIG5vbWVfbW90b3Jpc3RhIAogICBJTlRFR0VSIG51bWVyb19jb21wYXJ0aW1lbnRvcyAKICAgVkFSQ0hBUig1MCkgbnVtZXJvX25vdGFfZmlzY2FsIAogICBURVhUIG9ic2VydmFjYW9fY2FuY2VsYW1lbnRvIAogICBURVhUIG9ic2VydmFjYW9fZ2VyYWwgCiAgIFZBUkNIQVIoMTUwKSBvcmlnZW0gCiAgIFZBUkNIQVIoMTApIHBsYWNhIAogICBWQVJDSEFSKDEwKSBzdGF0dXNfcG9ydGFyaWEgCiAgIEJJR0lOVCB0ZXJtaW5hbF9pZCAKICAgQklHSU5UIHRyYW5zcG9ydGFkb3JhX2lkIAogICBCSUdJTlQgdXN1YXJpb19hcHJvdmFjYW9fc2FpZGFfaWQgCiAgIEJJR0lOVCB1c3VhcmlvX3JlZ2lzdHJvX2lkIAogICBOVU1FUklDKDEyLF8yKSB2b2x1bWVfbm90YV9maXNjYWxfbGl0cm9zIAp9CmNvbGV0YV9hbW9zdHJhIHsKIEJJR0lOVCBpZCBQSwogICBCSUdJTlQgYW1vc3RyYWRvcl9pZCAKICAgREFURVRJTUUgZGF0YV9ob3JhX2NvbGV0YSAKICAgSU5URUdFUiBudW1lcm9fY29sZXRhIAogICBWQVJDSEFSKDMwKSBzdGF0dXMgCiAgIEJJR0lOVCB1c3VhcmlvX3JlY2ViaW1lbnRvX2lkIAogICBCSUdJTlQgdmVpY3Vsb19pZCAKfQphbW9zdHJhIHsKIEJJR0lOVCBpZCBQSwogICBOVU1FUklDKDEyLF8yKSBjYXBhY2lkYWRlX2NvbXBhcnRpbWVudG9fbGl0cm9zIAogICBWQVJDSEFSKDMwKSBjb2RpZ29fYW1vc3RyYSAKICAgQklHSU5UIGNvbGV0YV9pZCAKICAgREFURVRJTUUgZGF0YV9ob3JhX2NvbGV0YSAKICAgREFURVRJTUUgZGF0YV9ob3JhX2ZpbV9hbmFsaXNlIAogICBEQVRFVElNRSBkYXRhX2hvcmFfcmVjb2xldGEgCiAgIERBVEVUSU1FIGRhdGFfaG9yYV9yZXByb3ZhY2FvIAogICBWQVJDSEFSKDEwKSBldGFwYV9hbmFsaXNlIAogICBWQVJDSEFSKDEwKSBpZGVudGlmaWNhZG9yX2NvbXBhcnRpbWVudG8gCiAgIEJPT0xFQU4gaXNfcmVjb2xldGEgCiAgIFRFWFQgbW90aXZvX3JlY29sZXRhIAogICBURVhUIG1vdGl2b19yZXByb3ZhY2FvIAogICBCSUdJTlQgb3BlcmFkb3JfaWQgCiAgIFZBUkNIQVIoMzApIG9yaWdlbV9wcm9jZWRpbWVudG8gCiAgIEJJR0lOVCBwcm9kdXRvX2lkIAogICBWQVJDSEFSKDkpIHN0YXR1c19yZXN1bHRhZG8gCiAgIE5VTUVSSUMoNSxfMikgdGVtcGVyYXR1cmFfY29sZXRhX2NlbHNpdXMgCiAgIEJJR0lOVCB1c3VhcmlvX3JlY29sZXRhX2lkIAogICBCSUdJTlQgdXN1YXJpb19yZXByb3ZhY2FvX2lkIAogICBCSUdJTlQgdmVpY3Vsb19pZCAKfQphbmFsaXNlX2Ftb3N0cmEgewogQklHSU5UIGlkIFBLCiAgIEJPT0xFQU4gYWd1YV9saXZyZSAKICAgQklHSU5UIGFtb3N0cmFfaWQgCiAgIEJJR0lOVCBhbmFsaXN0YV9pZCAKICAgVkFSQ0hBUig1MCkgYXNwZWN0byAKICAgVkFSQ0hBUig1MCkgY29yIAogICBEQVRFVElNRSBkYXRhX2hvcmFfYW5hbGlzZSAKICAgTlVNRVJJQyg4LF80KSBkZW5zaWRhZGVfa2dfbCAKICAgTlVNRVJJQyg2LF80KSBmYXRvcl9jb3JyZWNhbyAKICAgTlVNRVJJQyg1LF8yKSBncmF1X2lucG0gCiAgIEJJR0lOVCBsYWJvcmF0b3Jpb19pZCAKICAgTlVNRVJJQyg4LF80KSBtYXNzYV9lc3BlY2lmaWNhXzIwY19rZ19sIAogICBCT09MRUFOIG1hdGVyaWFsX3BhcnRpY3VsYWRvIAogICBWQVJDSEFSKDMwKSBudW1lcm9fYW1vc3RyYV9sYWIgCiAgIFRFWFQgb2JzZXJ2YWNvZXMgCiAgIE5VTUVSSUMoNSxfMikgdGVtcGVyYXR1cmFfZW5zYWlvX2NlbHNpdXMgCiAgIE5VTUVSSUMoOCxfMikgdGVvcl9hZ3VhX3BwbSAKICAgVkFSQ0hBUig1MCkgdGlwb19lc3BlY2lmaWNvX3Byb2R1dG8gCiAgIFZBUkNIQVIoNTApIHZpc3RvX2FuYWxpc3RhIAp9CmNvbXByb3ZhbnRlX2Ftb3N0cmEgewogQklHSU5UIGlkIFBLCiAgIFRFWFQgY29tcGxlbWVudG9fb2JzZXJ2YWNvZXMgCiAgIEJJR0lOVCBjb25nZW5lcmVfaWQgCiAgIEJJR0lOVCBjcmlhZG9fcG9yX3VzdWFyaW9faWQgCiAgIERBVEUgZGF0YV9nZXJhY2FvIAogICBOVU1FUklDKDgsXzQpIGRlbnNpZGFkZV8yMGNfYXB1cmFkYSAKICAgTlVNRVJJQyg2LF80KSBmYXRvcl9jb3JyZWNhbyAKICAgTlVNRVJJQyg1LF8yKSBncmF1X2lucG0gCiAgIFRJTUUgaG9yYV9nZXJhY2FvIAogICBWQVJDSEFSKDUwKSBsYW5jYW1lbnRvX3NpY29mIAogICBWQVJDSEFSKDUwKSBub3RhX2Zpc2NhbF9udW1lcm8gCiAgIFZBUkNIQVIoNTApIG51bWVyb19zaWNvZiAKICAgTlVNRVJJQygxMixfMikgcmVzdWx0YWRvX3ZhcmlhY2FvX2xpdHJvcyAKICAgVkFSQ0hBUigxMCkgc3RhdHVzIAogICBCSUdJTlQgdGFucXVlX2Rlc2NhcmdhX2lkIAogICBCSUdJTlQgdmVpY3Vsb19pZCAKICAgTlVNRVJJQygxMixfMikgdm9sdW1lXzIwY19hcHVyYWRvX2xpdHJvcyAKICAgTlVNRVJJQygxMixfMikgdm9sdW1lXzIwY19uZl9saXRyb3MgCiAgIE5VTUVSSUMoMTIsXzIpIHZvbHVtZV9hbWJpZW50ZV9hcHVyYWRvX2xpdHJvcyAKICAgTlVNRVJJQygxMixfMikgdm9sdW1lX2FtYmllbnRlX25mX2xpdHJvcyAKICAgTlVNRVJJQygxMixfMikgdm9sdW1lX3JldGlyYWRhX2xpdHJvcyAKfQpjb21wcm92YW50ZV9hbW9zdHJhX2l0ZW0gewogQklHSU5UIGlkIFBLCiAgIEJJR0lOVCBhbW9zdHJhX2lkIAogICBCSUdJTlQgY29tcHJvdmFudGVfaWQgCn0KaGlzdG9yaWNvX2VkaWNhb19jb21wcm92YW50ZSB7CiBCSUdJTlQgaWQgUEsKICAgQklHSU5UIGNvbXByb3ZhbnRlX2lkIAogICBEQVRFVElNRSBkYXRhX2hvcmEgCiAgIFRFWFQgZGVzY3JpY2FvX2FjYW8gCiAgIEJJR0lOVCB1c3VhcmlvX2lkIAp9Cmhpc3Rvcmljb19lZGljYW9fdmVpY3VsbyB7CiBCSUdJTlQgaWQgUEsKICAgVkFSQ0hBUigxMDApIGNhbXBvX2FsdGVyYWRvIAogICBEQVRFVElNRSBkYXRhX2hvcmEgCiAgIFRFWFQgbW90aXZvIAogICBCSUdJTlQgdXN1YXJpb19pZCAKICAgVEVYVCB2YWxvcl9hbnRlcmlvciAKICAgVEVYVCB2YWxvcl9ub3ZvIAogICBCSUdJTlQgdmVpY3Vsb19pZCAKfQpoaXN0b3JpY29fZWRpY2FvX2Ftb3N0cmEgewogQklHSU5UIGlkIFBLCiAgIEJJR0lOVCBhbW9zdHJhX2lkIAogICBWQVJDSEFSKDEwMCkgY2FtcG9fYWx0ZXJhZG8gCiAgIERBVEVUSU1FIGRhdGFfaG9yYSAKICAgVEVYVCBtb3Rpdm8gCiAgIEJJR0lOVCB1c3VhcmlvX2lkIAogICBURVhUIHZhbG9yX2FudGVyaW9yIAogICBURVhUIHZhbG9yX25vdm8gCn0KaGlzdG9yaWNvX2VkaWNhb19hbmFsaXNlIHsKIEJJR0lOVCBpZCBQSwogICBCSUdJTlQgYW5hbGlzZV9hbW9zdHJhX2lkIAogICBWQVJDSEFSKDEwMCkgY2FtcG9fYWx0ZXJhZG8gCiAgIERBVEVUSU1FIGRhdGFfaG9yYSAKICAgVEVYVCBtb3Rpdm8gCiAgIEJJR0lOVCB1c3VhcmlvX2lkIAogICBURVhUIHZhbG9yX2FudGVyaW9yIAogICBURVhUIHZhbG9yX25vdm8gCn0KdGVybWluYWwgMS0tMCsgbGFib3JhdG9yaW8gOiBoYXMKdGVybWluYWwgMS0tMCsgdGFucXVlIDogaGFzCnByb2R1dG8gMS0tMCsgdGFucXVlIDogaGFzCnByb2R1dG8gMS0tMCsgdmVpY3Vsb19wcm9kdXRvIDogaGFzCnZlaWN1bG8gMS0tMCsgdmVpY3Vsb19wcm9kdXRvIDogaGFzCmNvbmdlbmVyZSAxLS0wKyB2ZWljdWxvIDogaGFzCnVzdWFyaW8gb25lIG9yIHplcm8tLTArIHZlaWN1bG8gOiBoYXMKdHJhbnNwb3J0YWRvcmEgMS0tMCsgdmVpY3VsbyA6IGhhcwp1c3VhcmlvIDEtLTArIHZlaWN1bG8gOiBoYXMKdGVybWluYWwgMS0tMCsgdmVpY3VsbyA6IGhhcwp2ZWljdWxvIDEtLTArIGNvbGV0YV9hbW9zdHJhIDogaGFzCnVzdWFyaW8gb25lIG9yIHplcm8tLTArIGNvbGV0YV9hbW9zdHJhIDogaGFzCnVzdWFyaW8gb25lIG9yIHplcm8tLTArIGNvbGV0YV9hbW9zdHJhIDogaGFzCnByb2R1dG8gMS0tMCsgYW1vc3RyYSA6IGhhcwp1c3VhcmlvIG9uZSBvciB6ZXJvLS0wKyBhbW9zdHJhIDogaGFzCmNvbGV0YV9hbW9zdHJhIDEtLTArIGFtb3N0cmEgOiBoYXMKdXN1YXJpbyBvbmUgb3IgemVyby0tMCsgYW1vc3RyYSA6IGhhcwp1c3VhcmlvIG9uZSBvciB6ZXJvLS0wKyBhbW9zdHJhIDogaGFzCnZlaWN1bG8gMS0tMCsgYW1vc3RyYSA6IGhhcwphbW9zdHJhIDEtLTArIGFuYWxpc2VfYW1vc3RyYSA6IGhhcwpsYWJvcmF0b3JpbyBvbmUgb3IgemVyby0tMCsgYW5hbGlzZV9hbW9zdHJhIDogaGFzCnVzdWFyaW8gMS0tMCsgYW5hbGlzZV9hbW9zdHJhIDogaGFzCnZlaWN1bG8gMS0tMCsgY29tcHJvdmFudGVfYW1vc3RyYSA6IGhhcwpjb25nZW5lcmUgMS0tMCsgY29tcHJvdmFudGVfYW1vc3RyYSA6IGhhcwp1c3VhcmlvIDEtLTArIGNvbXByb3ZhbnRlX2Ftb3N0cmEgOiBoYXMKdGFucXVlIG9uZSBvciB6ZXJvLS0wKyBjb21wcm92YW50ZV9hbW9zdHJhIDogaGFzCmFtb3N0cmEgMS0tMCsgY29tcHJvdmFudGVfYW1vc3RyYV9pdGVtIDogaGFzCmNvbXByb3ZhbnRlX2Ftb3N0cmEgMS0tMCsgY29tcHJvdmFudGVfYW1vc3RyYV9pdGVtIDogaGFzCmNvbXByb3ZhbnRlX2Ftb3N0cmEgMS0tMCsgaGlzdG9yaWNvX2VkaWNhb19jb21wcm92YW50ZSA6IGhhcwp1c3VhcmlvIDEtLTArIGhpc3Rvcmljb19lZGljYW9fY29tcHJvdmFudGUgOiBoYXMKdmVpY3VsbyAxLS0wKyBoaXN0b3JpY29fZWRpY2FvX3ZlaWN1bG8gOiBoYXMKdXN1YXJpbyAxLS0wKyBoaXN0b3JpY29fZWRpY2FvX3ZlaWN1bG8gOiBoYXMKdXN1YXJpbyAxLS0wKyBoaXN0b3JpY29fZWRpY2FvX2Ftb3N0cmEgOiBoYXMKYW1vc3RyYSAxLS0wKyBoaXN0b3JpY29fZWRpY2FvX2Ftb3N0cmEgOiBoYXMKdXN1YXJpbyAxLS0wKyBoaXN0b3JpY29fZWRpY2FvX2FuYWxpc2UgOiBoYXMKYW5hbGlzZV9hbW9zdHJhIDEtLTArIGhpc3Rvcmljb19lZGljYW9fYW5hbGlzZSA6IGhhcw==)
