file = rev(list.files('results', 'annealing*'))[1]
dat = read.csv(paste('results/', file, sep=""), header=T)

algorithms = c("Base.version", "Version.1b", "Window.2", "Window.4", "Window.8")
cannonical_names = c("Base", "Base+", "Window 2", "Window 4", "Window 8")
color_set = c("green", "grey", "magenta", "cyan", "orange")

max_temp = max(dat$temp)
plot(c(), c(),
     type='l',
     xlim=c(1,max_temp),
     ylim=c(0,5),
     xlab="Temperature",
     ylab="Score",
     frame.plot=F
)
lines(seq(max_temp), dat$Base.version_score, col='green')
lines(seq(max_temp), dat$Version.1b_score, col='grey')
lines(seq(max_temp), dat$Window.2_score, col='magenta')
lines(seq(max_temp), dat$Window.4_score, col='cyan')
lines(seq(max_temp), dat$Window.8_score, col='orange')

plot(c(), c(),
     type='l',
     xlim=c(1,max_temp),
     ylim=c(0,20),
     xlab="Temperature",
     ylab="Path len",
     frame.plot=F
)
lines(seq(max_temp), dat$Base.version_len, col='green')
lines(seq(max_temp), dat$Version.1b_len, col='grey')
lines(seq(max_temp), dat$Window.2_len, col='magenta')
lines(seq(max_temp), dat$Window.4_len, col='cyan')
lines(seq(max_temp), dat$Window.8_len, col='orange')

plot(c(), c(),
     type='l',
     xlim=c(1,max_temp),
     ylim=c(0,20),
     xlab="Temperature",
     ylab="Conflicts solved",
     frame.plot=F
)
lines(seq(max_temp), dat$Base.version_conflicts, col='green')
lines(seq(max_temp), dat$Version.1b_conflicts, col='grey')
lines(seq(max_temp), dat$Window.2_conflicts, col='magenta')
lines(seq(max_temp), dat$Window.4_conflicts, col='cyan')
lines(seq(max_temp), dat$Window.8_conflicts, col='orange')

plot(c(), c(),
     type='l',
     xlim=c(1,max_temp),
     ylim=c(0,5),
     xlab="Temperature",
     ylab="Partial solved",
     frame.plot=F
)
lines(seq(max_temp), dat$Version.1b_partial, col='grey')
