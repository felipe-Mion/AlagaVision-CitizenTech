"""AlagaVision: analisa vídeos e fotos; perfis azul e café escuro; sem webcam."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np

from src.vision import Configuration, measure, annotate

ROOT = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser(description="AlagaVision | CitizenTech | FIAP")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--video", type=str, default=str(ROOT / "data/demonstracao_simulada.mp4"),
                        help="Vídeo (.mp4 ou .mov) gravado pelo iPhone 13 ou demonstração")
    source.add_argument("--camera", type=int, help="Opcional: câmera ligada ao computador")
    source.add_argument("--imagem", "--image", dest="imagem", type=str, help="Foto (.jpg, .jpeg, .png ou .bmp) do iPhone ou do computador")
    parser.add_argument("--liquido", choices=("azul", "cafe"), default="azul",
                        help="Perfil visual: azul (simulado) ou cafe (liquido escuro no copo)")
    parser.add_argument("--limiar-cafe", type=int, default=115,
                        help="Luminosidade máxima HSV-V 0..255 para detectar café escuro (padrão: 115)")
    parser.add_argument("--calibrar", action="store_true", help="Selecionar o interior do recipiente no primeiro frame")
    parser.add_argument("--config", default="calibracao_iphone.json", help="JSON da calibração (default: calibracao_iphone.json)")
    parser.add_argument("--roi", nargs=4, type=int, metavar=("X1", "Y1", "X2", "Y2"), help="Região manual em pixels")
    parser.add_argument("--max-cm", type=float, help="Altura física entre topo e base da ROI, em centímetros")
    parser.add_argument("--atencao-cm", type=float, help="Limiar de atenção em cm (padrão: 40%% da altura)")
    parser.add_argument("--critico-cm", type=float, help="Limiar crítico em cm (padrão: 70%% da altura)")
    parser.add_argument("--output", help="Arquivo anotado: .mp4 para vídeo, .jpg ou .png para imagem")
    parser.add_argument("--csv", default="resultados/leituras_demo.csv", help="CSV de medições")
    parser.add_argument("--no-display", action="store_true", help="Processar sem abrir janela")
    return parser.parse_args()


def load_config(args):
    obj = {}
    file = Path(args.config)
    if file.exists():
        obj = json.loads(file.read_text(encoding="utf-8"))
    roi = args.roi or obj.get("roi", [330, 120, 470, 426])
    max_cm = args.max_cm or obj.get("max_cm", 100.0)
    if max_cm <= 0:
        raise ValueError("--max-cm precisa ser maior que zero")
    if len(roi) != 4 or not all(isinstance(k, int) for k in roi):
        raise ValueError("--roi precisa ter quatro coordenadas inteiras")
    return tuple(roi), float(max_cm)


def fit_preview(frame, max_width=1200, max_height=800):
    """Reduz imagem apenas para exibição; preserva pixels originais na análise."""
    h, w = frame.shape[:2]
    scale = min(1.0, max_width / w, max_height / h)
    if scale < 1.0:
        return cv2.resize(frame, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA), scale
    return frame, 1.0


def choose_roi(frame, current_roi, args, max_cm):
    if not args.calibrar:
        return current_roi
    if args.no_display:
        raise SystemExit("--calibrar requer janela gráfica (retire --no-display)")
    print("\nCALIBRAÇÃO: marque uma região RETANGULAR dentro do copo, do topo da escala até a base (zero cm).")
    print("ENTER/ESPAÇO para confirmar; C para cancelar. Evite incluir a régua, a bancada, o fundo ou as bordas do copo.")
    print("O valor de --max-cm deve ser a distância física entre topo e base da seleção.\n")
    preview, scale = fit_preview(frame)
    rect = cv2.selectROI("Calibrar area monitorada", preview, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow("Calibrar area monitorada")
    x, y, w, h = [round(float(v) / scale) for v in rect]
    if w < 15 or h < 15:
        raise SystemExit("Calibração cancelada ou região muito pequena.")
    roi = (x, y, x + w, y + h)
    dest = Path(args.config)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"roi": list(roi), "max_cm": max_cm}, indent=2), encoding="utf-8")
    print(f"Calibração salva em {dest.resolve()}. Região={roi}; altura={max_cm} cm")
    return roi


def save_measurements(rows, target_name):
    target = Path(target_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["frame", "tempo_s", "nivel_estimado_cm", "alerta", "cobertura_hsv"])
        wr.writerows(rows)
    return target


def analyze_image(args, roi, max_cm):
    image_path = Path(args.imagem)
    if not image_path.is_file():
        raise SystemExit(f"Foto não encontrada: {image_path}")
    # imdecode permite inclusive nomes de arquivos com acentos no Windows.
    frame_data = np.fromfile(str(image_path), dtype=np.uint8)
    frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)
    if frame is None:
        raise SystemExit("Não foi possível abrir a foto. Use JPG ou PNG.")
    roi = choose_roi(frame, roi, args, max_cm)
    atencao = args.atencao_cm if args.atencao_cm is not None else 0.4 * max_cm
    critico = args.critico_cm if args.critico_cm is not None else 0.7 * max_cm
    if not (0 <= atencao < critico <= max_cm):
        raise SystemExit("Os limites precisam satisfazer 0 <= atenção < crítico <= máximo")
    cfg = Configuration(roi=roi, max_cm=max_cm, caution_cm=atencao, critical_cm=critico,
                        liquid_profile=args.liquido, coffee_value_max=args.limiar_cafe)
    try:
        det = measure(frame, cfg)
    except ValueError as exc:
        raise SystemExit(f"Calibração inválida para esta foto ({exc}). Execute com --calibrar.") from exc
    result = annotate(frame, det, cfg)
    target = Path(args.output or "resultados/foto_analisada.jpg")
    if target.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
        raise SystemExit("Para --imagem, --output precisa terminar em .jpg, .jpeg, .png ou .bmp")
    target.parent.mkdir(parents=True, exist_ok=True)
    ext = target.suffix.lower()
    ok, buffer = cv2.imencode(ext, result)
    if not ok:
        raise SystemExit("Falha ao salvar a foto analisada")
    buffer.tofile(str(target))
    csv_target = save_measurements([[0, 0.0, det.level_cm, det.status, det.confidence]], args.csv)
    print(f"1 imagem analisada | leitura em: {csv_target.resolve()}")
    print(f"Nível estimado: {det.level_cm if det.level_cm is not None else '--'} cm | Classificação: {det.status}")
    print(f"Imagem anotada: {target.resolve()}")
    if not args.no_display:
        preview, _ = fit_preview(result)
        cv2.imshow("AlagaVision | imagem (qualquer tecla para fechar)", preview)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def main():
    args = parse_args()
    roi, max_cm = load_config(args)
    if not (0 <= args.limiar_cafe <= 255):
        raise SystemExit("--limiar-cafe deve estar entre 0 e 255")
    if args.imagem is not None:
        analyze_image(args, roi, max_cm)
        return
    source = args.camera if args.camera is not None else args.video
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit("Não consegui abrir vídeo/câmera. Para .mov HEVC do iPhone, converta para H.264/MP4 ou selecione 'Mais Compatível' antes de gravar.")
    ret, first_frame = cap.read()
    if not ret:
        cap.release()
        raise SystemExit("O vídeo não contém quadros decodificáveis. Tente exportar como H.264/MP4.")
    roi = choose_roi(first_frame, roi, args, max_cm)
    atencao = args.atencao_cm if args.atencao_cm is not None else 0.4 * max_cm
    critico = args.critico_cm if args.critico_cm is not None else 0.7 * max_cm
    if not (0 <= atencao < critico <= max_cm):
        raise SystemExit("Os limites precisam satisfazer 0 <= atenção < crítico <= máximo")
    cfg = Configuration(roi=roi, max_cm=max_cm, caution_cm=atencao, critical_cm=critico,
                        liquid_profile=args.liquido, coffee_value_max=args.limiar_cafe)
    fps = cap.get(cv2.CAP_PROP_FPS) or 12.0
    if not (1 <= fps <= 240):
        fps = 12.0
    writer = None
    measurements = []
    try:
        frame = first_frame
        while True:
            count = len(measurements)
            det = measure(frame, cfg)
            result = annotate(frame, det, cfg, count)
            if args.output:
                if writer is None:
                    target = Path(args.output)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    writer = cv2.VideoWriter(str(target), cv2.VideoWriter_fourcc(*"mp4v"), fps,
                                             (frame.shape[1], frame.shape[0]))
                    if not writer.isOpened():
                        raise RuntimeError(f"Falha ao salvar vídeo MP4 em {target}")
                writer.write(result)
            measurements.append([count, round(count / fps, 3), det.level_cm, det.status, det.confidence])
            if not args.no_display:
                cv2.imshow("AlagaVision | tecla Q para encerrar", result)
                if cv2.waitKey(max(1, int(1000 / fps))) & 0xFF == ord("q"):
                    break
            ret, frame = cap.read()
            if not ret:
                break
    finally:
        cap.release()
        if writer:
            writer.release()
        if not args.no_display:
            cv2.destroyAllWindows()
    if not measurements:
        raise SystemExit("Vídeo sem quadros processados")
    target = save_measurements(measurements, args.csv)
    print(f"{len(measurements)} quadros analisados | leituras em: {target.resolve()}")
    print(f"Última classificação: {measurements[-1][3]}")
    if args.output:
        print(f"Vídeo anotado: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
