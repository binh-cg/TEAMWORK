from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS 
from werkzeug.security import generate_password_hash, check_password_hash 
from datetime import datetime
import random, string

app = Flask(__name__)
app.json.ensure_ascii = False
app.secret_key = 'Hệ Thống Quản Lý Vé Máy Bay'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///airline.db'
db = SQLAlchemy(app)

CORS(app)

#------- MODELS (CƠ SỞ DỮ LIỆU GỐC) -------#

class User(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    taiKhoan = db.Column(db.String(50), unique=True, nullable=False)
    matKhau = db.Column(db.String(100), nullable=False)
    hoTen = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    role = db.Column(db.String(20), default='khachhang')

class MayBay(db.Model):
    maMayBay = db.Column(db.String(20), primary_key=True)
    loaiMayBay = db.Column(db.String(50), nullable=False)
    tongSoGhe = db.Column(db.Integer, nullable=False)

class ChuyenBay(db.Model):
    maChuyenBay = db.Column(db.String(20), primary_key=True)
    maMayBay = db.Column(db.String(20), db.ForeignKey('may_bay.maMayBay'), nullable=False)
    sanBayDi = db.Column(db.String(50), nullable=False)
    sanBayDen = db.Column(db.String(50), nullable=False)
    ngayGioDi = db.Column(db.DateTime, nullable=False)
    ngayGioDen = db.Column(db.DateTime, nullable=False)
    giaVe = db.Column(db.Float, nullable=False)
    soGheTrong = db.Column(db.Integer, nullable=False)
    
    may_bay = db.relationship('MayBay', backref=db.backref('chuyen_bay', lazy=True))

class PhieuDatVe(db.Model):
    maDatVe = db.Column(db.String(20), primary_key=True)
    ngayDat = db.Column(db.DateTime, default=datetime.utcnow)
    trangThaiDatVe = db.Column(db.String(20), default='Chưa Thanh Toán')
    tongTien = db.Column(db.Float, nullable=False)
    phuongThucThanhToan = db.Column(db.String(20), nullable=False)
    ngayThanhToan = db.Column(db.DateTime)
    
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    chuyenbay_id = db.Column(db.String(20), db.ForeignKey('chuyen_bay.maChuyenBay'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('danh_sach_phieu_user', lazy=True))
    chuyenbay = db.relationship('ChuyenBay', backref=db.backref('danh_sach_phieu_chuyen_bay', lazy=True))

class HanhKhach(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    hoTen = db.Column(db.String(100), nullable=False)
    cccd = db.Column(db.String(20), unique=True, nullable=False)
    soDienThoai = db.Column(db.String(20), nullable=False)
    phieu_id = db.Column(db.String(20), db.ForeignKey('phieu_dat_ve.maDatVe'), nullable=False)
    
    phieu = db.relationship('PhieuDatVe', backref=db.backref('hanhkhach_list', lazy=True))

#------- WEB ROUTES GIAO DIỆN TRUYỀN THỐNG -------#

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chuyen-bay')
def xem_chuyen_bay():
    chuyen_bays = ChuyenBay.query.all()
    return render_template('chuyen_bay.html', chuyen_bays=chuyen_bays)

@app.route('/tra-cuu-ve')
def tra_cuu_ve():
    return render_template('search.html')

@app.route('/welcome')
def welcome():
    return "<h1>Chào mừng đến với Hệ Thống Quản Lý Vé Máy Bay</h1>"

@app.route('/tao-du-lieu')
def tao_du_lieu_route():
    return tao_du_lieu()

@app.route('/home')
def home():
    if 'user_id' in session:
        return render_template('home.html')
    flash('Bạn chưa đăng nhập hệ thống!', 'danger')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        taiKhoan = request.form['taiKhoan']
        matKhau = request.form['matKhau']
        user = User.query.filter_by(taiKhoan=taiKhoan).first()
        
        if user and check_password_hash(user.matKhau, matKhau):
            session['user_id'] = user.id
            session['hoTen'] = user.hoTen
            session['role'] = user.role
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Sai tài khoản hoặc mật khẩu!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Đăng xuất thành công!', 'success')
    return redirect(url_for('home'))

@app.route('/lien-he')
def lien_he():
    return render_template('contact.html')

#------- MỚI THÊM: CHỨC NĂNG TÁC NGHIỆP DÀNH CHO NHÂN VIÊN & ADMIN -------#

# Route Tra cứu toàn bộ thông tin tài khoản đặt vé, thông tin vé và hành khách đi kèm
@app.route('/quan-ly/khach-hang')
def quan_ly_khach_hang_route():
    if 'user_id' not in session or session.get('role') not in ['admin', 'nhanvien']:
        flash('Bạn không có quyền truy cập khu vực nghiệp vụ này!', 'danger')
        return redirect(url_for('login'))
    
    # Lấy toàn bộ phiếu đặt vé để bóc tách thông tin khách hàng toàn diện
    phieu_list = PhieuDatVe.query.all()
    return render_template('quan_ly_khach_hang.html', phieu_list=phieu_list)

# Route Hủy vé khách hàng bất kỳ (Dành cho Nhân viên và Admin)
@app.route('/quan-ly/huy-ve/<ma_ve>', methods=['POST'])
def quan_ly_huy_ve(ma_ve):
    if 'user_id' not in session or session.get('role') not in ['admin', 'nhanvien']:
        flash('Thao tác từ chối: Quyền hạn không hợp lệ!', 'danger')
        return redirect(url_for('login'))
        
    phieu = PhieuDatVe.query.get(ma_ve)
    if not phieu:
        flash('Không tìm thấy mã vé yêu cầu trên hệ thống!', 'danger')
        return redirect(url_for('quan_ly_khach_hang_route'))
        
    if phieu.trangThaiDatVe == 'Đã Hủy':
        flash('Vé này đã được hủy bỏ trước đó.', 'danger')
        return redirect(url_for('quan_ly_khach_hang_route'))
        
    # Hoàn trả số lượng ghế trống về cho Chuyến bay
    so_luong_hoan_ghe = HanhKhach.query.filter_by(phieu_id=ma_ve).count()
    chuyen_bay = ChuyenBay.query.get(phieu.chuyenbay_id)
    if chuyen_bay:
        chuyen_bay.soGheTrong += so_luong_hoan_ghe
        
    phieu.trangThaiDatVe = 'Đã Hủy'
    db.session.commit()
    flash(f'Đã thực thi hủy thành công vé {ma_ve}. Hệ thống đã hoàn trả {so_luong_hoan_ghe} ghế trống!', 'success')
    return redirect(url_for('quan_ly_khach_hang_route'))


#------- MỚI THÊM: CHỨC NĂNG ĐẶC ĐỊNH CHO TỐI CAO ADMIN -------#

# Route xem danh sách nhân viên vận hành hệ thống
@app.route('/admin/nhan-vien')
def quan_ly_nhan_vien_route():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Khu vực hạn chế: Chỉ dành riêng cho Quản trị viên tối cao!', 'danger')
        return redirect(url_for('home'))
        
    nhan_vien_list = User.query.filter_by(role='nhanvien').all()
    return render_template('quan_ly_nhan_vien.html', nhan_vien_list=nhan_vien_list)

# Route xóa/sa thải tài khoản nhân viên
@app.route('/admin/xoa-nhan-vien/<user_id>', methods=['POST'])
def xoa_nhan_vien(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Từ chối thực thi: Bạn không phải Admin!', 'danger')
        return redirect(url_for('home'))
        
    nv = User.query.get(user_id)
    if nv and nv.role == 'nhanvien':
        ten_nv = nv.hoTen
        db.session.delete(nv)
        db.session.commit()
        flash(f'Đã xóa bỏ hoàn toàn nhân viên {ten_nv} khỏi cơ sở dữ liệu!', 'success')
    else:
        flash('Đối tượng không tồn tại hoặc không thể tác động xóa!', 'danger')
        
    return redirect(url_for('quan_ly_nhan_vien_route'))


#------- API ROUTES (CỔNG RA CHO FRONTEND ĐỘC LẬP) -------#

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Thiếu dữ liệu gửi lên"}), 400
    tai_khoan = data.get('taiKhoan')
    mat_khau = data.get('matKhau')
    user = User.query.filter_by(taiKhoan=tai_khoan).first()
    if user and check_password_hash(user.matKhau, mat_khau):
        return jsonify({
            "status": "success",
            "message": "Đăng nhập hệ thống thành công!",
            "user": {"id": user.id, "taiKhoan": user.taiKhoan, "hoTen": user.hoTen, "role": user.role}
        }), 200
    return jsonify({"status": "error", "message": "Tài khoản hoặc mật khẩu không chính xác!"}), 401

@app.route('/register', methods=['GET', 'POST'])
def web_register():
    if request.method == 'POST':
        tai_khoan = request.form.get('username')
        mat_khau = request.form.get('password')
        ho_ten = request.form.get('fullname')
        confirm = request.form.get('confirm_password')

        if mat_khau != confirm:
            flash('Mật khẩu xác nhận không khớp!', 'danger')
            return redirect(url_for('web_register'))
        if User.query.filter_by(taiKhoan=tai_khoan).first():
            flash('Tài khoản đã tồn tại!', 'danger')
            return redirect(url_for('web_register'))

        ma_user = 'U' + ''.join(random.choices(string.digits, k=4))
        new_user = User(id=ma_user, taiKhoan=tai_khoan, matKhau=generate_password_hash(mat_khau), hoTen=ho_ten, role='khachhang')
        db.session.add(new_user)
        db.session.commit()
        flash('Đăng ký thành công! Hãy đăng nhập.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/api/logout', methods=['POST', 'GET'])
def api_logout():
    return jsonify({"status": "success", "message": "Đăng xuất hệ thống thành công!"}), 200

@app.route('/api/chuyen-bay', methods=['GET'])
def api_chuyen_bay():
    chuyen_bays = ChuyenBay.query.all()
    result = []
    for cb in chuyen_bays:
        result.append({
            "maChuyenBay": cb.maChuyenBay, "maMayBay": cb.maMayBay, "sanBayDi": cb.sanBayDi, "sanBayDen": cb.sanBayDen,
            "ngayGioDi": cb.ngayGioDi.strftime("%Y-%m-%d %H:%M"), "ngayGioDen": cb.ngayGioDen.strftime("%Y-%m-%d %H:%M"),
            "giaVe": cb.giaVe, "soGheTrong": cb.soGheTrong
        })
    return jsonify({"status": "success", "chuyenBays": result}), 200

@app.route('/api/chuyen-bay/search', methods=['GET'])
def api_chuyen_bay_search():
    san_bay_di = request.args.get('sanBayDi')
    san_bay_den = request.args.get('sanBayDen')
    ngay_gio_di = request.args.get('ngayGioDi')
    query = ChuyenBay.query
    if san_bay_di: query = query.filter(ChuyenBay.sanBayDi.like(f'%{san_bay_di}%'))
    if san_bay_den: query = query.filter(ChuyenBay.sanBayDen.like(f'%{san_bay_den}%'))
    chuyen_bays = query.all()
    result = []
    for cb in chuyen_bays:
        if ngay_gio_di and cb.ngayGioDi.strftime("%Y-%m-%d") != ngay_gio_di: continue
        result.append({
            "maChuyenBay": cb.maChuyenBay, "maMayBay": cb.maMayBay, "sanBayDi": cb.sanBayDi, "sanBayDen": cb.sanBayDen,
            "ngayGioDi": cb.ngayGioDi.strftime("%Y-%m-%d %H:%M"), "ngayGioDen": cb.ngayGioDen.strftime("%Y-%m-%d %H:%M"),
            "giaVe": cb.giaVe, "soGheTrong": cb.soGheTrong
        })
    return jsonify({"status": "success", "chuyenBays": result}), 200 

@app.route('/search', methods=['GET'])
def web_search():
    san_bay_di = request.args.get('sanBayDi')
    san_bay_den = request.args.get('sanBayDen')
    ngay_gio_di = request.args.get('ngayGioDi')
    query = ChuyenBay.query
    if san_bay_di: query = query.filter(ChuyenBay.sanBayDi.like(f"%{san_bay_di}%"))
    if san_bay_den: query = query.filter(ChuyenBay.sanBayDen.like(f"%{san_bay_den}%"))
    chuyen_bays = query.all()
    ket_qua_loc = []
    for cb in chuyen_bays:
        if ngay_gio_di and cb.ngayGioDi.strftime('%Y-%m-%d') != ngay_gio_di: continue
        ket_qua_loc.append(cb)
    return render_template('search_results.html', chuyen_bays=ket_qua_loc)

@app.route('/api/dat-ve', methods=['POST'])
def api_dat_ve():
    data = request.get_json()
    if not data: return jsonify({"status": "error", "message": "Thiếu dữ liệu gửi lên"}), 400
    user_id = data.get('userId')
    chuyenbay_id = data.get('chuyenBayId')
    phuong_thuc_thanh_toan = data.get('phuongThucThanhToan')
    danh_sach_hanh_khach = data.get('hanhKhachList', [])
    user = User.query.get(user_id)
    chuyen_bay = ChuyenBay.query.get(chuyenbay_id)
    if not user or not chuyen_bay: return jsonify({"status": "error", "message": "Người dùng hoặc chuyến bay không tồn tại!"}), 404
    so_luong_mua = len(danh_sach_hanh_khach) if danh_sach_hanh_khach else 1
    if chuyen_bay.soGheTrong < so_luong_mua: return jsonify({"status": "error", "message": f"Chuyến bay không đủ chỗ!"}), 400
    tong_tien = chuyen_bay.giaVe * so_luong_mua
    ma_dat_ve = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    try:
        phieu_dat_ve = PhieuDatVe(maDatVe=ma_dat_ve, tongTien=tong_tien, phuongThucThanhToan=phuong_thuc_thanh_toan, user_id=user_id, chuyenbay_id=chuyenbay_id)
        db.session.add(phieu_dat_ve)
        for hk in danh_sach_hanh_khach:
            hanh_khach = HanhKhach(id='HK' + ''.join(random.choices(string.digits, k=4)), hoTen=hk.get('hoTen'), cccd=hk.get('cccd'), soDienThoai=hk.get('soDienThoai'), phieu_id=ma_dat_ve)
            db.session.add(hanh_khach)
        chuyen_bay.soGheTrong -= so_luong_mua
        db.session.commit()
        return jsonify({"status": "success", "message": "Đặt vé thành công!", "maDatVe": ma_dat_ve}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Lỗi hệ thống: {str(e)}"}), 500

@app.route('/api/ve/thanh-toan/<ma_ve>', methods=['PUT'])
def api_thanh_toan_ve(ma_ve):
    phieu = PhieuDatVe.query.get(ma_ve)
    if not phieu: return jsonify({"status": "error", "message": "Không tìm thấy mã vé này"}), 404
    if phieu.trangThaiDatVe != 'Chưa Thanh Toán': return jsonify({"status": "error", "message": f"Vé này đang ở trạng thái: {phieu.trangThaiDatVe}"}), 400
    phieu.trangThaiDatVe = 'Đã Thanh Toán'
    phieu.ngayThanhToan = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "success", "message": "Cập nhật trạng thái Đã Thanh Toán thành công!"}), 200

@app.route('/api/ve/huy/<ma_ve>', methods=['PUT'])
def api_huy_ve(ma_ve):
    phieu = PhieuDatVe.query.get(ma_ve)
    if not phieu: return jsonify({"status": "error", "message": "Không tìm thấy mã vé"}), 404
    if phieu.trangThaiDatVe == 'Đã Hủy': return jsonify({"status": "error", "message": "Vé này đã được hủy trước đó rồi"}), 400
    so_luong_hoan_ghe = HanhKhach.query.filter_by(phieu_id=ma_ve).count()
    chuyen_bay = ChuyenBay.query.get(phieu.chuyenbay_id)
    if chuyen_bay: chuyen_bay.soGheTrong += so_luong_hoan_ghe
    phieu.trangThaiDatVe = 'Đã Hủy'
    db.session.commit()
    return jsonify({"status": "success", "message": f"Hủy vé thành công."}), 200

@app.route('/dat-ve', methods=['GET', 'POST'])
def web_dat_ve():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập tài khoản để tiến hành đặt vé!', 'danger')
        return redirect(url_for('login'))
    ma_cb = request.args.get('id')
    chuyen_bay = ChuyenBay.query.get(ma_cb)
    if not chuyen_bay:
        flash('Chuyến bay không tồn tại!', 'danger')
        return redirect(url_for('xem_chuyen_bay'))
    if request.method == 'POST':
        ho_ten = request.form.get('hoTen')
        cccd = request.form.get('cccd')
        so_dt = request.form.get('soDienThoai')
        phuong_thuc = request.form.get('phuongThucThanhToan')
        if chuyen_bay.soGheTrong <= 0:
            flash('Chuyến bay này đã hết chỗ trống mất rồi!', 'danger')
            return redirect(url_for('xem_chuyen_bay'))
        ma_dat_ve = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        try:
            phieu = PhieuDatVe(maDatVe=ma_dat_ve, tongTien=chuyen_bay.giaVe, phuongThucThanhToan=phuong_thuc, user_id=session['user_id'], chuyenbay_id=ma_cb)
            db.session.add(phieu)
            hanh_khach = HanhKhach(id='HK' + ''.join(random.choices(string.digits, k=4)), hoTen=ho_ten, cccd=cccd, soDienThoai=so_dt, phieu_id=ma_dat_ve)
            db.session.add(hanh_khach)
            chuyen_bay.soGheTrong -= 1
            db.session.commit()
            return render_template('xac_nhan_ve.html', ma_dat_ve=ma_dat_ve, cb=chuyen_bay, ho_ten=ho_ten, cccd=cccd)
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi đặt vé: {str(e)}', 'danger')
    return render_template('dat_ve.html', cb=chuyen_bay)

@app.route('/ve-cua-toi')
def ve_cua_toi():
    if 'user_id' not in session: return redirect(url_for('login'))
    phieu_list = PhieuDatVe.query.filter_by(user_id=session['user_id']).all()
    return render_template('ve_cua_toi.html', phieu_list=phieu_list)

@app.route('/huy-ve/<ma_ve>', methods=['POST'])
def web_huy_ve(ma_ve):
    if 'user_id' not in session: return redirect(url_for('login'))
    phieu = PhieuDatVe.query.get(ma_ve)
    if not phieu or phieu.user_id != session['user_id']: return redirect(url_for('ve_cua_toi'))
    if phieu.trangThaiDatVe == 'Đã Hủy': return redirect(url_for('ve_cua_toi'))
    so_ghe = HanhKhach.query.filter_by(phieu_id=ma_ve).count()
    cb = ChuyenBay.query.get(phieu.chuyenbay_id)
    if cb: cb.soGheTrong += so_ghe
    phieu.trangThaiDatVe = 'Đã Hủy'
    db.session.commit()
    return redirect(url_for('ve_cua_toi'))

@app.route('/thanh-toan/<ma_ve>', methods=['POST'])
def web_thanh_toan(ma_ve):
    if 'user_id' not in session: return redirect(url_for('login'))
    phieu = PhieuDatVe.query.get(ma_ve)
    if not phieu or phieu.user_id != session['user_id']: return redirect(url_for('ve_cua_toi'))
    phieu.trangThaiDatVe = 'Đã Thanh Toán'
    phieu.ngayThanhToan = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('ve_cua_toi'))

def tao_du_lieu():
    if User.query.first(): return 'Dữ liệu mẫu đã có sẵn.'
    db.session.add(User(id='U001', taiKhoan='admin', matKhau=generate_password_hash('admin123'), hoTen='Chủ Trì Hệ Thống', email='admin@pcsd.com', role='admin'))
    db.session.add(User(id='U002', taiKhoan='nhanvien', matKhau=generate_password_hash('nv123'), hoTen='Nhân Viên Bán Vé', email='nhanvien@pcsd.com', role='nhanvien'))
    db.session.add(User(id='U003', taiKhoan='khachhang', matKhau=generate_password_hash('kh123'), hoTen='Khách Hàng Thân Thiết', email='khachhang@gmail.com', role='khachhang'))
    db.session.add(MayBay(maMayBay='MB001', loaiMayBay='Airbus A320', tongSoGhe=189))
    db.session.add(MayBay(maMayBay='MB002', loaiMayBay='Boeing 737', tongSoGhe=178))
    db.session.add(ChuyenBay(maChuyenBay='VN004', maMayBay='MB001', sanBayDi='Hà Nội(HAN)', sanBayDen='Hồ Chí Minh(SGN)', ngayGioDi=datetime(2026, 5, 23, 10, 0), ngayGioDen=datetime(2026, 5, 23, 12, 0), giaVe=1500000, soGheTrong=189))
    db.session.add(ChuyenBay(maChuyenBay='VJ008', maMayBay='MB002', sanBayDi='Huế(HUI)', sanBayDen='Hà Nội (HAN)', ngayGioDi=datetime(2026, 6, 15, 14, 20), ngayGioDen=datetime(2026, 6, 15, 16, 10), giaVe=1000000, soGheTrong=178))
    db.session.commit()
    return 'Hệ thống đã khởi tạo dữ liệu mẫu thành công.'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        tao_du_lieu()
    app.run(debug=True)