import os
import subprocess
import time
import multiprocessing
import sys
import argparse

def obter_header_ppm(file_path):
    with open(file_path, "rb") as f:
        tipo = f.readline().strip() 
        linha = f.readline().strip()
        while linha.startswith(b'#'): linha = f.readline().strip()
        largura, altura = map(int, linha.split())
        v_max = f.readline().strip()
        while v_max.startswith(b'#'): v_max = f.readline().strip()
        return largura, altura, int(v_max), f.tell()

def barra_progresso(atual, total):
    largura_barra = 40
    progresso = atual / total
    cheios = int(largura_barra * progresso)
    barra = '█' * cheios + '-' * (largura_barra - cheios)
    sys.stdout.write(f'\rProgresso: |{barra}| {progresso*100:6.1f}% ({atual}/{total})')
    sys.stdout.flush()

def chamar_caixa_preta(args_tarefa):
    c_script, f_in, f_out = args_tarefa
    subprocess.run(
        [sys.executable, c_script, f_in, f_out],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return True

def rodar_teste_unico(pasta_fatias, n_threads, t_serial_referencia):
    fatias = sorted([f for f in os.listdir(pasta_fatias) if f.endswith(".ppm")])
    num_fatias = len(fatias)
    
    pasta_tmp = f"tmp_{n_threads}th"
    os.makedirs(pasta_tmp, exist_ok=True)

    tarefas = [
        ("conversoremescalacinza.py", os.path.join(pasta_fatias, f), 
         os.path.join(pasta_tmp, f.replace(".ppm", "_gray.ppm")))
        for f in fatias
    ]

    print(f"\n🚀 Executando experimento isolado com {n_threads} thread(s)...")
    
    inicio = time.time()
    concluidos = 0
    barra_progresso(0, num_fatias)

    with multiprocessing.Pool(processes=n_threads) as pool:
        for _ in pool.imap_unordered(chamar_caixa_preta, tarefas):
            concluidos += 1
            barra_progresso(concluidos, num_fatias)
    
    tempo_total = time.time() - inicio
    print(f"\n\n⏱️  Tempo Final: {tempo_total:.4f} segundos")

    # Mesclagem (Merge)
    res_final = f"resultado_{n_threads}th.ppm"
    print(f"📦 Gerando arquivo final: {res_final}...")
    
    # Pegar metadados da primeira fatia de saída
    l_f, a_total, v_f, _ = obter_header_ppm(tarefas[0][2])
    for _, _, c_out in tarefas[1:]:
        _, h, _, _ = obter_header_ppm(c_out)
        a_total += h

    with open(res_final, "wb") as fout:
        fout.write(f"P6\n{l_f} {a_total}\n{v_f}\n".encode("ascii"))
        for _, _, c_out in tarefas:
            with open(c_out, "rb") as f_p:
                _, _, _, off = obter_header_ppm(c_out)
                f_p.seek(off)
                while True:
                    chunk = f_p.read(1024*1024)
                    if not chunk: break
                    fout.write(chunk)

    # Limpeza
    for _, _, c_out in tarefas: os.remove(c_out)
    os.rmdir(pasta_tmp)

    # --- CÁLCULO DE SPEEDUP E EFICIÊNCIA ---
    print("\n" + "="*50)
    print(f"RESULTADOS PARA {n_threads} THREADS")
    print("-" * 50)
    print(f"Tempo: {tempo_total:.4f}s")
    
    if t_serial_referencia > 0:
        speedup = t_serial_referencia / tempo_total
        eficiencia = (speedup / n_threads) * 100
        print(f"Speedup: {speedup:.2f}x")
        print(f"Eficiência: {eficiencia:.2f}%")
    else:
        print("Speedup: (Rode com 1 thread primeiro para obter a base)")
    print("="*50 + "\n")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("pasta", help="Pasta com as 100 fatias")
    parser.add_argument("threads", type=int, help="Quantidade de threads para este teste")
    parser.add_argument("--serial", type=float, default=0.0, help="Tempo do teste serial (1 thread) para calcular speedup")
    
    args = parser.parse_args()
    rodar_teste_unico(args.pasta, args.threads, args.serial)