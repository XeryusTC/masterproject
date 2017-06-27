library(ggplot2)
library(reshape)

file = rev(list.files('results', 'benchmark*'))[1]
dat = read.csv(paste('results/', file, sep=""), header=T)
algorithms = colnames(dat)[2:ncol(dat)]

results = dat
for (algorithm in algorithms) {
    # Because 'order' returns the indices we need to use it to select data
     results[algorithm] = dat[order(dat[algorithm]), algorithm]
}
#plot(results[,1], results[,c(2:ncol(results))])
molten = melt(results, id.vars="instance")
ggplot(molten, aes(x=instance, y=value*1000, color=variable)) +
    geom_line() +
    scale_x_continuous(name="Instance",
                       minor_breaks=NULL) +
    scale_y_log10(name="Time (ms)",
                  limits=c(5,2000),
                  breaks=c(1, 10, 100, 1000, 2000),
                  minor_breaks=NULL) +
    labs(colour="Legend") +
    theme_minimal()
