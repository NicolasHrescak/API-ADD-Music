from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///musica.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secretkey'  # Substitua por uma chave mais segura

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MODELO DE USUÁRIO PARA AUTENTICAÇÃO
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

# CARREGAMENTO DO USUÁRIO
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# MODELOS DE MÚSICA, ÁLBUM E ARTISTA
class Musica(db.Model):
    id_musica = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    duracao = db.Column(db.String(10), nullable=False)
    artista_id = db.Column(db.Integer, db.ForeignKey('artista.id_artista'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id_album'), nullable=False)
    artista = db.relationship('Artista', back_populates='musicas')
    album = db.relationship('Album', back_populates='musicas')

class Album(db.Model):
    id_album = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    n_faixas = db.Column(db.Integer, nullable=False)
    artista_id = db.Column(db.Integer, db.ForeignKey('artista.id_artista'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    gravadora = db.Column(db.String(100), nullable=False)
    artista = db.relationship('Artista', back_populates='albuns')
    musicas = db.relationship('Musica', back_populates='album')

class Artista(db.Model):
    id_artista = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    genero = db.Column(db.String(100), nullable=False)
    gravadora = db.Column(db.String(100), nullable=False)
    albuns = db.relationship('Album', back_populates='artista')
    musicas = db.relationship('Musica', back_populates='artista')

with app.app_context():
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Conta criada com sucesso!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        # Confere se o usuário e a senha estão corretos
        if user and check_password_hash(user.password, password):
            login_user(user)  # Usando login_user para gerenciar a sessão
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('home'))  # Redireciona para a página home após login
        else:
            flash('Nome de usuário ou senha incorretos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Usando logout_user para sair
    flash('Desconectado com sucesso', 'info')
    return redirect(url_for('login'))

# ROTAS PRINCIPAIS (PROTEGIDAS)
@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/add_musica', methods=['GET', 'POST'])
@login_required
def add_musica():
    if request.method == 'POST':
        titulo = request.form['titulo']
        duracao = request.form['duracao']
        nome_artista = request.form['artista']
        nome_album = request.form['album']
        musica_existente = Musica.query.filter_by(titulo=titulo).first()
        album_existente = Album.query.filter_by(titulo=nome_album).first()
        artista_existente = Artista.query.filter_by(nome=nome_artista).first()
        if artista_existente and album_existente and musica_existente is None:
            new_musica = Musica(titulo=titulo, duracao=duracao, artista=artista_existente, album=album_existente)
            db.session.add(new_musica)
            db.session.commit()
            flash('Música cadastrada com sucesso!')
            return redirect(url_for('musicas'))
        flash('Erro ao cadastrar música.')
    return render_template('form.html')

@app.route('/add_album', methods=['GET', 'POST'])
@login_required
def add_album():
    if request.method == 'POST':
        titulo = request.form['titulo']
        faixas = request.form['faixas']
        nome_artista = request.form['artista']
        gravadora = request.form['gravadora']
        data_str = request.form['data']
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
        album_existente = Album.query.filter_by(titulo=titulo).first()
        artista_existente = Artista.query.filter_by(nome=nome_artista).first()
        if album_existente is None and artista_existente:
            new_album = Album(titulo=titulo, n_faixas=faixas, artista=artista_existente, gravadora=gravadora, date=data)
            db.session.add(new_album)
            db.session.commit()
            flash('Álbum cadastrado com sucesso!')
            return redirect(url_for('albuns'))
        flash('Erro ao cadastrar álbum.')
    return render_template('album_form.html')

@app.route('/add_artista', methods=['GET', 'POST'])
@login_required
def add_artista():
    if request.method == 'POST':
        nome = request.form['nome']
        genero = request.form['genero']
        gravadora = request.form['gravadora']
        artista_existente = Artista.query.filter_by(nome=nome).first()
        if artista_existente is None:
            new_artista = Artista(nome=nome, genero=genero, gravadora=gravadora)
            db.session.add(new_artista)
            db.session.commit()
            flash('Artista cadastrado com sucesso!')
            return redirect(url_for('artistas'))
        flash('Erro ao cadastrar artista.')
    return render_template('artista_form.html')

@app.route('/musicas')
@login_required
def musicas():
    lista_musicas = Musica.query.all()
    return render_template('musicas.html', lista_musicas=lista_musicas)

@app.route('/artistas')
@login_required
def artistas():
    lista_artistas = Artista.query.all()
    return render_template('artistas.html', lista_artistas=lista_artistas)

@app.route('/albuns')
@login_required
def albuns():
    lista_albuns = Album.query.all()
    return render_template('albuns.html', lista_albuns=lista_albuns)

@app.route('/update_musica/<int:musica_id>', methods=['GET', 'POST'])
@login_required
def update_musica(musica_id):
    # Buscar a música existente pelo ID
    musica = Musica.query.get_or_404(musica_id)

    if request.method == 'POST':
        # Coletar os dados enviados do formulário
        titulo = request.form['titulo']
        duracao = request.form['duracao']
        nome_artista = request.form['artista']
        nome_album = request.form['album']

        # Verificar se o artista e o álbum existem no banco de dados
        artista_existente = Artista.query.filter_by(nome=nome_artista).first()
        album_existente = Album.query.filter_by(titulo=nome_album).first()

        if artista_existente and album_existente:
            # Atualizar os atributos da música
            musica.titulo = titulo
            musica.duracao = duracao
            musica.artista = artista_existente
            musica.album = album_existente

            # Salvar as mudanças no banco de dados
            db.session.commit()

            return 'Música atualizada com sucesso!'
        else:
            if not artista_existente:
                return 'Artista não encontrado.'
            if not album_existente:
                return 'Álbum não encontrado.'
    # Exibir o formulário de atualização preenchido com os dados atuais
    return render_template('update_musica.html', musica=musica)

@app.route('/update_album/<int:album_id>', methods=['GET', 'POST'])
@login_required
def update_album(album_id):
    # Buscar a música existente pelo ID
    album = Album.query.get_or_404(album_id)

    if request.method == 'POST':
        # Coletar os dados enviados do formulário
        titulo = request.form['titulo']
        faixas = request.form['faixas']
        nome_artista = request.form['artista']
        gravadora = request.form['gravadora']
        data = request.form['data']

        # Verificar se o artista e o álbum existem no banco de dados
        artista_existente = Artista.query.filter_by(nome=nome_artista).first()

        if artista_existente:
            # Atualizar os atributos da música
            album.titulo = titulo
            album.faixas = faixas
            album.artista = nome_artista
            album.gravadora = gravadora
            album.data = data

            # Salvar as mudanças no banco de dados
            db.session.commit()

            return 'Álbum atualizada com sucesso!'
        else:
            if not artista_existente:
                return 'Artista não encontrado.'
    # Exibir o formulário de atualização preenchido com os dados atuais
    return render_template('update_album.html', album=album)

@app.route('/update_artista/<int:artista_id>', methods=['GET', 'POST'])
@login_required
def update_artista(artista_id):
    # Buscar o artista existente pelo ID
    artista = Artista.query.get_or_404(artista_id)

    if request.method == 'POST':
        # Coletar os dados enviados do formulário
        nome = request.form['nome']
        genero = request.form['genero']
        gravadora = request.form['gravadora']

        # Atualizar os atributos da música
        artista.nome = nome
        artista.genero = genero
        artista.gravadora = gravadora

        # Salvar as mudanças no banco de dados
        db.session.commit()

        return 'Artista atualizado(a) com sucesso!'
    # Exibir o formulário de atualização preenchido com os dados atuais
    return render_template('update_artista.html', artista=artista)

@app.route('/delete_musica/<int:musica_id>')
@login_required
def delete_musica(musica_id):
    musica = Musica.query.get_or_404(musica_id)  # Correct usage
    db.session.delete(musica)  # Delete the object directly
    db.session.commit()  # Commit the changes
    return 'Música deletada com sucesso!'

@app.route('/delete_artista/<int:artista_id>')
@login_required
def delete_artista(artista_id):
    artista = Artista.query.get_or_404(artista_id)  # Correct usage
    db.session.delete(artista)  # Delete the object directly
    db.session.commit()  # Commit the changes
    return 'Artista deletado(a) com sucesso!'

@app.route('/delete_album/<int:album_id>')
@login_required
def delete_album(album_id):
    album = Album.query.get_or_404(album_id)  # Correct usage
    db.session.delete(album)  # Delete the object directly
    db.session.commit()  # Commit the changes
    return 'Álbum deletado com sucesso!'

# MAIN
if __name__ == '__main__':
    app.run(debug=True)
