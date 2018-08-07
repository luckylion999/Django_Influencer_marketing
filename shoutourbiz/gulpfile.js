var gulp = require('gulp');
var replace = require('gulp-replace');

gulp.task('prep-local', function() {
	gulp.src(['manage.py'])
		.pipe(replace('prod_settings', 'local_settings'))
		.pipe(replace('dev_settings', 'local_settings'))
		.pipe(gulp.dest(''));

	gulp.src(['shoutourbiz/wsgi.py'])
		.pipe(replace('prod_settings', 'local_settings'))
		.pipe(replace('dev_settings', 'local_settings'))
		.pipe(gulp.dest('shoutourbiz/'));
});

gulp.task('prep-dev', function() {
	gulp.src(['manage.py'])
		.pipe(replace('local_settings', 'dev_settings'))
		.pipe(replace('prod_settings', 'dev_settings'))
		.pipe(gulp.dest(''));

	gulp.src(['shoutourbiz/wsgi.py'])
		.pipe(replace('local_settings', 'dev_settings'))
		.pipe(replace('prod_settings', 'dev_settings'))
		.pipe(gulp.dest('shoutourbiz/'));
});

gulp.task('prep-prod', function() {
	gulp.src(['manage.py'])
		.pipe(replace('local_settings', 'prod_settings'))
		.pipe(replace('dev_settings', 'prod_settings'))
		.pipe(gulp.dest(''));

	gulp.src(['shoutourbiz/wsgi.py'])
		.pipe(replace('local_settings', 'prod_settings'))
		.pipe(replace('dev_settings', 'prod_settings'))
		.pipe(gulp.dest('shoutourbiz/'));
});