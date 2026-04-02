import os
import sys
import mmap

def obter_header_ppm(f):
    """Lê o cabeçalho PPM e lida com possíveis comentários."""
    tipo = f.readline().strip() # P6
    if tipo != b'P6':
        raise ValueError("Apenas formato PPM P6 é suportado.")
    
    linha = f.readline().strip()
    while linha.startswith(b'#'): 
        linha = f.readline().strip()
    
    largura, altura = map(int, linha.split())
    
    linha = f.readline().strip()
    while linha.startswith(b'#'): 
        linha = f.readline().strip()
    
    v_max = int(linha)
    return largura, altura, v_max, f.tell()

def barra_progresso(atual, total):
    comprimento = 40
    percentual = atual / total
    blocos = int(comprimento * percentual)
    barra = "█" * blocos + "-" * (comprimento - blocos)
    sys.stdout.write(f"\rProgresso: |{barra}| {percentual*100:6.1f}% ({atual}/{total})")
    sys.stdout.flush()

def fatiar_em_100(arquivo_entrada):
    # 1. Gerar nome da pasta automaticamente
    # Pega o nome do arquivo sem a extensão .ppm
    nome_base = os.path.splitext(os.path.basename(arquivo_entrada))[0]
    pasta_destino = f"fatias_{nome_base}"

    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)
        print(f"📁 Pasta automática criada: '{pasta_destino}'")
    else:
        print(f"📂 Usando pasta existente: '{pasta_destino}'")

    # 2. Abrir arquivo original
    try:
        with open(arquivo_entrada, "rb") as f:
            largura, altura, v_max, offset_orig = obter_header_ppm(f)
            
            num_fatias = 100
            linhas_por_fatia = altura // num_fatias
            sobra_linhas = altura % num_fatias
            
            print(f"🖼️  Imagem: {largura}x{altura} | 🔪 Criando {num_fatias} arquivos...")

            # Memory Mapping para velocidade máxima
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                cursor_linha = 0
                
                for i in range(num_fatias):
                    # Distribui as linhas que sobraram
                    h_fatia = linhas_por_fatia + (1 if i < sobra_linhas else 0)
                    
                    nome_fatia = os.path.join(pasta_destino, f"fatia_{i:03d}.ppm")
                    
                    with open(nome_fatia, "wb") as wf:
                        # Header válido para cada pedaço
                        header = f"P6\n{largura} {h_fatia}\n{v_max}\n".encode("ascii")
                        wf.write(header)
                        
                        # Cálculo de bytes exato
                        inicio_bytes = offset_orig + (cursor_linha * largura * 3)
                        fim_bytes = inicio_bytes + (h_fatia * largura * 3)
                        
                        wf.write(mm[inicio_bytes:fim_bytes])
                    
                    cursor_linha += h_fatia
                    barra_progresso(i + 1, num_fatias)

        print(f"\n\n✅ Concluído! Os 100 arquivos estão em: '{pasta_destino}'")
        return pasta_destino

    except FileNotFoundError:
        print(f"\n❌ Erro: O arquivo '{arquivo_entrada}' não foi encontrado.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python fatiador_auto.py imagem.ppm")
        sys.exit(1)

    arquivo = sys.argv[1]
    fatiar_em_100(arquivo)