from app import app, db, lm
from flask import render_template, flash, redirect, session, g, url_for, request
from .form import LoginForm, RegisterForm, EditForm, PostForm, SearchForm, ChangePasswordForm
from .models import User, Post
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from config import POSTS_PER_PAGE, MAX_SEARCH_RESULTS, FOLLOWERS_PER_PAGE

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()
        g.search_form = SearchForm()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required
def index(page=1):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
        db.session.add(post)
        db.session.commit()
        flash ('Your post is now live!')
        return redirect(url_for('index'))
    posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    return render_template('index.html', title='Home', form=form, posts=posts)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash ('You have not registed yet!')
            return redirect(url_for('login'))
        if user.check_password(form.password.data):
            flash ('You have successfully login!')
            session['remember_me'] = form.remember_me.data
            login_user(user, session['remember_me'])
            return redirect(request.args.get('next') or url_for('index'))
        flash('Wrong Password!')
        return redirect(url_for('login'))        
    return render_template('login.html', title='Sign in', form=form)

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).count() != 0:
            flash ('Email Already Exists!')
            return redirect(url_for('register'))
        if User.query.filter_by(nickname=form.nickname.data).count() != 0:
            flash ('Nickname Already Exists!')
            return redirect(url_for('register'))
        user = User(email=form.email.data, nickname=form.nickname.data)
        db.session.add(user)
        db.session.commit()
        flash ('Registration Succeeds!')
        db.session.add(user.follow(user))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html',title='Register', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User not found.')
        return redirect(url_for('index'))
    posts = user.posts.paginate(page, POSTS_PER_PAGE, False)
    return render_template('user.html', user=user, posts=posts)

@app.route('/edit', methods=['GET','POST'])
@login_required
def edit():
    form = EditForm()
    if form.validate_on_submit():
        if User.query.filter_by(nickname=form.nickname.data).first() is not None \
           and g.user.nickname != form.nickname.data:
            flash ('Nickname Already Exists!')
            return redirect(url_for('edit')) 
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user', nickname=g.user.nickname))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html',form=form)

@app.route('/change_password', methods=['GET','POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not g.user.check_password(form.old_password.data):
            flash ('Wrong password!')
            return redirect(url_for('change_password'))
        if form.new_password.data != form.confirm_password.data:
            flash ('Please confirm your password!')
            return redirect(url_for('change_password'))
        g.user.password = form.new_password.data
        db.session.add(g.user)
        db.session.commit()
        flash ('You have changed your password.')
        return redirect(url_for('user', nickname=g.user.nickname))
    return render_template('change_password.html', form=form)

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash ('User not found.')
        return redirect(url_for('index'))
    if user == g.user:
        flash ('You have already followed yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.follow(user)
    if u is None:
        flash('Cannot follow' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash ('You are now following' + nickname + '!')
    return redirect(url_for('user', nickname=nickname))


@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):    
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash ('User not found.')
        return redirect(url_for('index'))
    if user == g.user:
        flash ('You cannot unfollow yourself!')
        return redirect(url_for('user', nickname=nickname))
    u = g.user.unfollow(user)
    if u is None:
        flash('Cannot unfollow' + nickname + '.')
        return redirect(url_for('user', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash ('You have stopped following' + nickname + '.')
    return redirect(url_for('user', nickname=nickname))

@app.route('/search', methods=['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query=g.search_form.search.data))

@app.route('/search_results/<query>')
@login_required
def search_results(query):
    results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
    return render_template('search_results.html', query=query, results=results)

@app.route('/delete/<id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    post=Post.query.filter_by(id=id).first()
    if post is None:
        flash('Post not found.')
        return redirect(url_for('index'))
    if post.author != g.user:
        flash('You cannot delete this post!')
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted.')
    return redirect(url_for('index'))

@app.route('/user/<nickname>/followerlist')
@app.route('/user/<nickname>/followerlist/<int:page>')
@login_required
def followerlist(nickname, page=1):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User not found.')
        return redirect(url_for('index'))
    follower_list = user.followers.paginate(page, FOLLOWERS_PER_PAGE, False)
    return render_template('followerlist.html', user=user, follower_list=follower_list)

@app.route('/user/<nickname>/followedlist')
@app.route('/user/<nickname>/followedlist/<int:page>')
@login_required
def followedlist(nickname, page=1):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User not found.')
        return redirect(url_for('index'))
    followed_list = user.followed.paginate(page, FOLLOWERS_PER_PAGE, False)
    return render_template('followedlist.html', user=user, followed_list=followed_list)
