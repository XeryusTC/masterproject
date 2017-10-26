file = rev(list.files('results', 'cache*'))[1]
dat.cache = read.csv(paste('results/', file, sep=""), header=T)

algorithms = c("Base", "Plus", "Window2", "Window4", "Window8")
cannonical.names = c("OD+ID", "NPPCPF", "PPCPF", "PPCPF+", "WPPCPF-2", "WPPCPF-4", "WPPCPF-8")
cannonical.names.cache = cannonical.names[3:7]
color.set = c("red", "blue", "green", "grey", "magenta", "cyan", "orange")
color.set.cache = color.set[3:7]

len.cache = length(unique(dat.cache$instance))
base.nocache    = sort(dat.cache[dat.cache$algorithm=='Base' &
                                     dat.cache$cache=='False',]$time * 1000)
plus.nocache    = sort(dat.cache[dat.cache$algorithm=='Plus' &
                                     dat.cache$cache=='False',]$time * 1000)
window2.nocache = sort(dat.cache[dat.cache$algorithm=='Window2' &
                                     dat.cache$cache=='False',]$time * 1000)
window4.nocache = sort(dat.cache[dat.cache$algorithm=='Window4' &
                                     dat.cache$cache=='False',]$time * 1000)
window8.nocache = sort(dat.cache[dat.cache$algorithm=='Window8' &
                                     dat.cache$cache=='False',]$time * 1000)
base.cache      = sort(dat.cache[dat.cache$algorithm=='Base' &
                                     dat.cache$cache=='True',]$time * 1000)
plus.cache      = sort(dat.cache[dat.cache$algorithm=='Plus' &
                                     dat.cache$cache=='True',]$time * 1000)
window2.cache   = sort(dat.cache[dat.cache$algorithm=='Window2' &
                                     dat.cache$cache=='True',]$time * 1000)
window4.cache   = sort(dat.cache[dat.cache$algorithm=='Window4' &
                                     dat.cache$cache=='True',]$time * 1000)
window8.cache   = sort(dat.cache[dat.cache$algorithm=='Window8' &
                                     dat.cache$cache=='True',]$time * 1000)

plot(c(), c(),
     type='l',
     log='y',
     col='red',
     xlim=c(1,len.cache),
     ylim=c(5, 2000),
     xlab='Instance',
     ylab='Time (ms)',
     frame.plot=F,
     yaxs="i"
)
lines(seq(length(base.nocache)), base.nocache, col=color.set.cache[1], lty=3)
lines(seq(length(plus.nocache)), plus.nocache, col=color.set.cache[2])
lines(seq(length(window2.nocache)), window2.nocache, col=color.set.cache[3])
lines(seq(length(window4.nocache)), window4.nocache, col=color.set.cache[4])
lines(seq(length(window8.nocache)), window8.nocache, col=color.set.cache[5])
lines(seq(length(base.cache)), base.cache, col=color.set.cache[1], lty=2)
lines(seq(length(plus.cache)), plus.cache, col=color.set.cache[2], lty=2)
lines(seq(length(window2.cache)), window2.cache, col=color.set.cache[3], lty=2)
lines(seq(length(window4.cache)), window4.cache, col=color.set.cache[4], lty=2)
lines(seq(length(window8.cache)), window8.cache, col=color.set.cache[5], lty=2)
legend("bottomright",
       legend=cannonical.names.cache[c(1,3,5)],
       col=color.set.cache[c(1,3,5)],
       pch=16)
aggr.cache = aggregate(. ~ num.agents + algorithm + cache, data=dat.cache,
                       FUN=mean)
cache.lm = lm(time ~ num.agents + algorithm * cache, data=aggr.cache)
cache.anova = aov(cache.lm)
cache.sum = summary(cache.anova)[[1]]
