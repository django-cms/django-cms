Contribution Guide
==================

For contributing to django-cms follow these steps:

You need either [GIT](http://git-scm.com/) or [mercurial](http://www.selenic.com/mercurial/) with [hg-git](http://hg-git.github.com/) extension installed.

You need an account on [github](http://www.github.com)

On github you can see all the open [tickets](http://github.com/digi604/django-cms-2.0/issues) be sure to check there first before you open a new one.

Goto the [project-page](http://github.com/digi604/django-cms-2.0/) and click on the fork button.
This creates your own repository of django-cms2 and enables you to "push" to this repository.



On your fork you should see "Your Clone URL:". Copy the url and "clone" it with git or hg-git.

	$ git clone YOURURL
	
or 
	
	$ hg gclone YOURURL

Make your changes and commit.

	$ git commit
	
or 
	
	$ hg commit
	
After you are finished you can push to github. 

	$ git push origin
	
or 
	
	$ hg gpush origin

After you have pushed your changes should show up in the project [network](http://github.com/digi604/django-cms-2.0/network).

You can no press on "pull request" to send the project leaders a message of what your changes contain and alert them to that there are new commits ready to be applied.

After some time you local and github repository is probably outdated.
To get the newest changesets add a new remote:

	$ git remote add upstream git://github.com/digi604/django-cms-2.0.git
	
or 
	
	$ hg gremote add upstream git://github.com/digi604/django-cms-2.0.git
	
After this you can "fetch" from upstream:

	$ git fetch upstream 	(only download)
	$ git pull upstream 	(download and merge)
	
or 
	
	$ hg gfetch upstream 	(download)
	$ hg update 			(merge)

Now your repository is up to date again.

If you have questions read some tutorials about git or hg or ask on IRC or the mailing list.
