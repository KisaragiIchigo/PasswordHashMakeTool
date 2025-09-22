import os
from PySide6.QtCore import Qt, QRect, QPoint, QEvent
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QApplication, QTextBrowser, QDialog, QSizePolicy, QGraphicsDropShadowEffect
)

from processor import sha256_hex, validate_passwords
from utils import try_icon_path, open_env_editor
from config import load_config, save_config

# ===== UI定数 =====
PRIMARY_COLOR    = "#4169e1"
HOVER_COLOR      = "#7000e0"
TITLE_COLOR      = "#FFFFFF"
TEXT_COLOR       = "#FFFFFF"
WINDOW_BG        = "rgba(255,255,255,0)"
CARD_BG          = "rgba(5,5,51,200)"
CARD_BORDER      = "3px solid rgba(65,105,255,255)"
PANEL_BG         = "#579cdd"
RADIUS_WINDOW    = 18
RADIUS_CARD      = 16
RADIUS_PANEL     = 10
RADIUS_BTN       = 8
GAP_DEFAULT      = 10
PADDING_CARD     = 16
RESIZE_MARGIN    = 8

def build_qss(compact: bool) -> str:
    glass_grad = (
        "qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        "stop:0 rgba(255,255,255,50), stop:0.5 rgba(200,220,255,25), stop:1 rgba(255,255,255,8))"
    )
    bg_image = "none" if compact else glass_grad
    return f"""
        QWidget#rootBg {{ background-color:{WINDOW_BG}; border-radius:{RADIUS_WINDOW}px; }}
        QWidget#card {{
            background-color:{CARD_BG};
            border:{CARD_BORDER};
            border-radius:{RADIUS_CARD}px;
            background-image:{bg_image};
            background-repeat:no-repeat;
        }}
        .Panel {{
            background-color:{PANEL_BG};
            border-radius:{RADIUS_PANEL}px;
            border:1px solid rgba(0,0,0,120);
            color:{TEXT_COLOR};
        }}
        QLabel, QLineEdit {{ color:{TEXT_COLOR}; }}
        QLineEdit {{
            background:#ffe4e1; color:#000; border:1px solid #888; border-radius:4px; padding:4px;
        }}
        QPushButton {{
            background:{PRIMARY_COLOR}; color:white; border:none; border-radius:{RADIUS_BTN}px;
            padding:6px 10px;
        }}
        QPushButton:hover {{ background:{HOVER_COLOR}; }}
        QLabel#titleLabel {{ color:{TITLE_COLOR}; font-weight:bold; }}
        QTextBrowser#readmeViewer {{
            color:#ffe4e1; background:#333; border-radius:{RADIUS_PANEL}px; padding:8px;
        }}
    """

def apply_drop_shadow(w: QWidget) -> QGraphicsDropShadowEffect:
    eff = QGraphicsDropShadowEffect(w)
    eff.setBlurRadius(28)
    eff.setOffset(0, 3)
    c = QColor(0, 0, 0); c.setAlphaF(0.18)
    eff.setColor(c)
    w.setGraphicsEffect(eff)
    return eff

README_MD = """# パスワードハッシュ生成ツール ©️2025 KisaragiIchigo

## 概要
- パスワードを **二重入力チェック** して **SHA-256** でハッシュ化
- 生成結果は **自動でクリップボードにコピー**
- Windowsなら **環境変数ダイアログ** をワンクリックで起動

## 使い方
1. パスワードを2回入力
2. 「ハッシュ生成」をクリック
3. ハッシュが表示されます（自動コピー）
4. 必要なら「環境変数を開く」ボタンから設定
"""

class ReadmeDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("README ©️2025 KisaragiIchigo")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(520, 360)

        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        bg = QWidget(); bg.setObjectName("rootBg"); outer.addWidget(bg)
        lay = QVBoxLayout(bg); lay.setContentsMargins(GAP_DEFAULT,GAP_DEFAULT,GAP_DEFAULT,GAP_DEFAULT)

        card = QWidget(); card.setObjectName("card"); lay.addWidget(card)
        cardLay = QVBoxLayout(card); cardLay.setContentsMargins(PADDING_CARD,PADDING_CARD,PADDING_CARD,PADDING_CARD)
        title = QLabel("README"); title.setObjectName("titleLabel")
        cardLay.addWidget(title)

        viewer = QTextBrowser(); viewer.setObjectName("readmeViewer")
        viewer.setMarkdown(README_MD); viewer.setOpenExternalLinks(True)
        viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cardLay.addWidget(viewer, 1)

        btn_row = QHBoxLayout(); btn_close = QPushButton("閉じる"); btn_close.clicked.connect(self.accept)
        btn_row.addStretch(1); btn_row.addWidget(btn_close)
        cardLay.addLayout(btn_row)

        self.setStyleSheet(build_qss(compact=False))

        # ドラッグ移動
        self._dragging = False; self._drag_off = QPoint()
        for w in (bg, card): w.installEventFilter(self)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.MouseButtonPress and e.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_off = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            return True
        elif e.type() == QEvent.MouseMove and self._dragging and (e.buttons() & Qt.LeftButton):
            self.move(e.globalPosition().toPoint() - self._drag_off); return True
        elif e.type() == QEvent.MouseButtonRelease:
            self._dragging = False; return True
        return super().eventFilter(obj, e)

class PasswordHashWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("パスワードハッシュ生成ツール ©️2025 KisaragiIchigo")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(520, 360)

        ic = try_icon_path()
        if ic: self.setWindowIcon(QIcon(ic))

        self.cfg = load_config()

        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        self.bg = QWidget(); self.bg.setObjectName("rootBg"); outer.addWidget(self.bg)

        bgLay = QVBoxLayout(self.bg); bgLay.setContentsMargins(GAP_DEFAULT,GAP_DEFAULT,GAP_DEFAULT,GAP_DEFAULT)
        self.card = QWidget(); self.card.setObjectName("card"); bgLay.addWidget(self.card)
        self._shadow = apply_drop_shadow(self.card)

        lay = QVBoxLayout(self.card); lay.setContentsMargins(PADDING_CARD,PADDING_CARD,PADDING_CARD,PADDING_CARD)

        title_row = QHBoxLayout()
        self.title_label = QLabel("パスワードハッシュ生成ツール"); self.title_label.setObjectName("titleLabel")
        title_row.addWidget(self.title_label)
        title_row.addStretch(1)
        self.btn_min = QPushButton("🗕"); self.btn_min.setFixedSize(28,28); self.btn_min.setToolTip("最小化")
        self.btn_max = QPushButton("🗖"); self.btn_max.setFixedSize(28,28); self.btn_max.setToolTip("最大化/復元")
        self.btn_close = QPushButton("ｘ"); self.btn_close.setFixedSize(28,28); self.btn_close.setToolTip("閉じる")
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self._toggle_max_restore)
        self.btn_close.clicked.connect(self.close)
        title_row.addWidget(self.btn_min); title_row.addWidget(self.btn_max); title_row.addWidget(self.btn_close)
        lay.addLayout(title_row)

        panel = QWidget(); panel.setProperty("class", "Panel")
        form = QVBoxLayout(panel); form.setContentsMargins(10,10,10,10); form.setSpacing(8)

        lbl1 = QLabel("パスワードを入力してください:")
        self.ed1 = QLineEdit(); self.ed1.setEchoMode(QLineEdit.Password)
        lbl2 = QLabel("パスワードを再入力してください:")
        self.ed2 = QLineEdit(); self.ed2.setEchoMode(QLineEdit.Password)
        self.msg = QLabel(""); self.msg.setStyleSheet("color:#ffd6d6;")

        btn_row = QHBoxLayout()
        self.btn_hash = QPushButton("ハッシュ生成"); self.btn_hash.clicked.connect(self._on_hash)
        self.btn_env  = QPushButton("環境変数を開く"); self.btn_env.clicked.connect(self._on_open_env)
        self.btn_readme = QPushButton("README"); self.btn_readme.clicked.connect(self._on_readme)
        btn_row.addWidget(self.btn_hash); btn_row.addWidget(self.btn_env); btn_row.addWidget(self.btn_readme)

        note = QLabel("(例) 新規作成 → [変数名] PASSWORD_HASH → [変数値] 貼り付け")

        form.addWidget(lbl1); form.addWidget(self.ed1)
        form.addWidget(lbl2); form.addWidget(self.ed2)
        form.addWidget(self.msg)
        form.addLayout(btn_row)
        form.addWidget(note)

        lay.addWidget(panel, 1)

        self._apply_compact(self.isMaximized())

        # ドラッグ/リサイズ
        self._dragging = False; self._drag_off = QPoint()
        self._resizing = False; self._resize_edges = ""; self._start_geo = None; self._start_mouse = None
        for w in (self.bg, self.card): w.setMouseTracking(True); w.installEventFilter(self)

        # 位置/サイズ復元
        w = self.cfg.get("window", {})
        self.resize(w.get("w", 560), w.get("h", 380))
        if w.get("x") is not None and w.get("y") is not None:
            self.move(w["x"], w["y"])

        self.setStyleSheet(build_qss(compact=self.isMaximized()))

    # ==== Handlers ====
    def _on_hash(self):
        ok, err = validate_passwords(self.ed1.text(), self.ed2.text())
        if not ok:
            self.msg.setText(err); self.msg.setStyleSheet("color:#ff6b6b;"); return
        hashed = sha256_hex(self.ed1.text())
        QApplication.clipboard().setText(hashed)
        QMessageBox.information(self, "結果", f"ハッシュ:\n{hashed}\n\nクリップボードへコピーしました。")

    def _on_open_env(self):
        success, msg = open_env_editor()
        if not success:
            QMessageBox.warning(self, "環境変数", msg)

    def _on_readme(self):
        dlg = ReadmeDialog(self); dlg.setModal(True); dlg.exec()

    # ==== Frameless: maximize/restore ====
    def _toggle_max_restore(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def changeEvent(self, e):
        super().changeEvent(e)
        if e.type() == QEvent.WindowStateChange:
            self._apply_compact(self.isMaximized())

    def _apply_compact(self, compact: bool):
        self.setStyleSheet(build_qss(compact))
        if hasattr(self, "_shadow"): self._shadow.setEnabled(not compact)
        self.btn_max.setText("❏" if self.isMaximized() else "🗖")

    # ==== Drag & Resize ====
    def eventFilter(self, obj, e):
        if obj is self.bg:
            if e.type() == QEvent.MouseButtonPress and e.button() == Qt.LeftButton:
                pos = self.mapFromGlobal(e.globalPosition().toPoint())
                edges = self._edge_at(pos)
                if edges:
                    self._resizing = True; self._resize_edges = edges
                    self._start_geo = self.geometry(); self._start_mouse = e.globalPosition().toPoint()
                else:
                    self._dragging = True
                    self._drag_off = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            elif e.type() == QEvent.MouseMove:
                if self._resizing:
                    self._do_resize(e.globalPosition().toPoint()); return True
                if self._dragging and (e.buttons() & Qt.LeftButton) and not self.isMaximized():
                    self.move(e.globalPosition().toPoint() - self._drag_off); return True
                self._update_cursor(self._edge_at(self.mapFromGlobal(e.globalPosition().toPoint())))
            elif e.type() == QEvent.MouseButtonRelease:
                self._resizing = False; self._dragging = False; return True
        return super().eventFilter(obj, e)

    def _edge_at(self, pos) -> str:
        m = RESIZE_MARGIN; r = self.bg.rect(); edges = ""
        if pos.y() <= m: edges += "T"
        if pos.y() >= r.height()-m: edges += "B"
        if pos.x() <= m: edges += "L"
        if pos.x() >= r.width()-m: edges += "R"
        return edges

    def _update_cursor(self, edges: str):
        if edges in ("TL","BR"): self.setCursor(Qt.SizeFDiagCursor)
        elif edges in ("TR","BL"): self.setCursor(Qt.SizeBDiagCursor)
        elif edges in ("L","R"): self.setCursor(Qt.SizeHorCursor)
        elif edges in ("T","B"): self.setCursor(Qt.SizeVerCursor)
        else: self.setCursor(Qt.ArrowCursor)

    def _do_resize(self, gpos):
        dx = gpos.x() - self._start_mouse.x()
        dy = gpos.y() - self._start_mouse.y()
        geo = self._start_geo; x,y,w,h = geo.x(),geo.y(),geo.width(),geo.height()
        minw, minh = self.minimumSize().width(), self.minimumSize().height()
        if "L" in self._resize_edges:
            new_w = max(minw, w - dx); x += (w - new_w); w = new_w
        if "R" in self._resize_edges: w = max(minw, w + dx)
        if "T" in self._resize_edges:
            new_h = max(minh, h - dy); y += (h - new_h); h = new_h
        if "B" in self._resize_edges: h = max(minh, h + dy)
        self.setGeometry(x, y, w, h)

    def closeEvent(self, e):
        g = self.geometry()
        self.cfg["window"] = {"w": g.width(), "h": g.height(), "x": g.x(), "y": g.y()}
        save_config(self.cfg)
        return super().closeEvent(e)
