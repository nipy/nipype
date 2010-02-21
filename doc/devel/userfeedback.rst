=============
User Feedback
=============

Below are user feedback on pipeline usage.

User 1
======

[...] I have to say, though, now that my pipelines are up and running, I'm about 95% satisfied with the whole thing.  Not sure how I'll feel when I want to go do something new and different, but still, so far so good.


- what features of the current setup do you like/dislike?
    * Likes: text-based interaction, ease of edits, batch processing, nice output storage hierarchy
    * Dislikes: separate pkg.Module().inputs_help() and pkg.Module().outputs_help() functions.  Although I've gotten used to this, it would be so much nicer if there were a single something like help(spm.Coregister) that just gave me everything..  Also, I really wish that it didn't give you error messages that are related to the behind-the-scenes stuff (like "XY is deprecated" when you run the pipeline initially, or "option cwd not allowed" during pipeline.run(), etc.) and unrelated to your inputs.  or at least if it said what you are supposed to do / think / care about such messages.


- what features do you wish were available?
    (this is kind of like the "functionality" question below - not sure what your features / functionality distinction is, so feel free to consider my responses to either as both)
    * more informative error messages.  It's nice to know which module failed, but it would be awesome if the pipeline error message itself could help indicate /why/ (i.e. communicate helpful error messages from the modules back to the ipython interface or something).


- if you were using nipype at an earlier stage and stopped, what made you stop?
    * I stopped and restarted again, but that was long ago, and mucho progress was made in the interim, it seemed.


- how steep did you feel was the learning curve? what kind of tutorials would have helped?
    * very steep.  AFNI used to have nice tutorials that explained the rationale of the neuroimaging analysis steps alongside the relevant AFNI tools that made them happen. (http://afni.nimh.nih.gov/afni/doc/howto)  A similar step-by-step guide (rather than just that big bucket Tutorial, which, while very helpful and well commented, is still rather daunting) would be a plus.  see, e.g.: http://afni.nimh.nih.gov/pub/dist/HOWTO//howto/ht01_ARzs/html/index.shtml and in particular http://afni.nimh.nih.gov/pub/dist/HOWTO//howto/ht01_ARzs/html/ARzs_analyze.shtml


- do you know you can visualize a simple and detailed visual representation of your workflow with export_graph()? if so, is it useful?
    * yes and I LOVE this feature.  It was also very very helpful in explaining how the pipeline worked when I gave a tutorial to YYYY.


- what missing functionality would you really like?
    * (1) easier integration w/ Freesurfer.  The surface-based pipeline we have is good, but I could never replicate that from scratch if I wanted to try something a little different.  all of this lh / rh stuff and iterating -- pipeline should (ideally) be able to figure out whether it needed to do that sort of thing behind-the-scenes.
    * (2) afni modules?  hello! 
    * (3) of course, that GUI for building pipelines would be nice :),
    * (4) oh man I wish I wish it could be strictly terminal-based and that there was some way to repress the ridiculous X-windows requirements of SPM,
    * (5) the output written to the screen during a running pipeline is not very good for seeing how "far along" it is, especially since it seems to run multiple subjects in parallel (?) or in very strange orders at least.  While I'm dreaming, maybe some sort of multifunctional display (like htop has) that shows you individual subject progress and overall progress and line-by-line output still... just dreaming here, but that would be nice for batches. 
    * (6) Also if one subject fails, maybe it could just drop that subject and the error messages until the end and keep running the pipeline on everyone else?  for me it's usually something stupid like I got the onsets wrong or the wrong dicoms, and then if I walk away from the computer and it stops halfway, I lose all that processing time when it could still have been doing everyone else.


- does the ability to mix programs from different packages really appeal to you? or is the learning curve to understand these different packages too great and makes you to stick to what you know best?
    * This I think is the #1 advantage of pipeline over batching by hand in bash or matlab.  The ease of integration across packages is really the most meaningful contribution of the pipeline to the NI community, imho.

User 2
======

1.  online documentation has improved greatly - it's very helpful to have clear definitions of input and output parameters/options, for example.
2.  error messages (and detailed crashdumps) are also very helpful - nice to be able to see exactly where the script is crashing (specifically, what lines, inputs, etc.)
3.  for event-related paradigms (i haven't even looked at ours yet), is there a way to feed a spm.mat file into the pipeline?  i've spoken to several people who already have onsets and other model information in a .mat file, which they would like to be able to feed into the pipeline (as opposed to writing out onsets in python).
4.  i do have the export_graph() line in my script, but i haven't looked at the output, to be perfectly honest.  what's the best way to view the visual output on the cluster?  where does it output this picture?
5.  i know that my whole lab group and i love the ability to mix and match different packages, which really makes nipype so appealing.  ...  took me a little while to get used to the python syntax, but once i familiarized myself with the input/output module syntax, things became much clearer.
