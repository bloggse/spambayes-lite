# not sure where this should go yet.
import config
import copy
import os

# NOTE: The Wizard works from a *complete* copy of the standard options
# but with an extra "Wizard" section to maintain state etc for the wizard.
# This initial option set may or may not have had values copied from the
# real runtime config - this allows either a "re-configure" or a
# "clean configure".
# Thus, the Wizard still uses standard config option where suitable - eg
# filter.watch_folder_ids
wizard_defaults = {
    "Wizard" : (
        ("preparation", "How prepared? radio on welcome", 0,
            """""",
        config.INTEGER, config.RESTORE),
        ("need_train", "Will moving to the train page actually train?", True,
            """""",
        config.BOOLEAN, config.RESTORE),
        ("will_train_later", "The user opted to cancel and train later", False,
            """""",
        config.BOOLEAN, config.RESTORE),
        # Spam
        ("spam_folder_name", "Name of spam folder - ignored if ID set", "Spam",
            """""",
            "", config.RESTORE),
        # unsure
        ("unsure_folder_name", "Name of unsure folder - ignored if ID set", "Maybe Spam",
            """""",
            "", config.RESTORE),
        ("temp_training_names", "", [], "", "", config.RESTORE),
    ),
}

def InitWizardConfig(manager, new_config, from_existing):
    manager.wizard_classifier_data = None # this is hacky
    new_config.filter.watch_folder_ids = []
    new_config.filter.watch_include_sub = False
    
    wc = new_config.wizard
    if from_existing:
        ids = copy.copy(manager.config.filter.watch_folder_ids)
        for id in ids:
            # Only get the folders that actually exist.
            if manager.message_store.GetFolder(id) is not None:
                new_config.filter.watch_folder_ids.append(id)
    if not new_config.filter.watch_folder_ids:
        for folder in manager.message_store.YieldReceiveFolders():
            new_config.filter.watch_folder_ids.append(folder.GetID())
    if from_existing:
        fc = manager.config.filter
        if fc.spam_folder_id:
            folder = manager.message_store.GetFolder(fc.spam_folder_id)
            if folder is not None:
                new_config.filter.spam_folder_id = folder.GetID()
                wc.spam_folder_name = ""
        if fc.unsure_folder_id:
            folder = manager.message_store.GetFolder(fc.unsure_folder_id)
            if folder is not None:
                new_config.filter.unsure_folder_id = folder.GetID()
                wc.unsure_folder_name = ""
        tc = manager.config.training
        if tc.ham_folder_ids:
            new_config.training.ham_folder_ids = tc.ham_folder_ids
        if tc.spam_folder_ids:
            new_config.training.spam_folder_ids = tc.spam_folder_ids
    if new_config.training.ham_folder_ids or new_config.training.spam_folder_ids:
        wc.preparation = 1 # "already prepared"

def _CreateFolder(manager, name, comment):
    try:
        root = manager.message_store.GetRootFolder()
        new_folder = root.CreateFolder(name, comment, open_if_exists = True)
        return new_folder
    except:
        msg = "There was an error creating the folder named '%s'\r\n" \
                "Please restart Outlook and try again" % name
        manager.ReportError(msg)
        return None
    
def CommitWizardConfig(manager, wc):
    # Create the ham and spam folders, if necessary.
    manager.config.filter.watch_folder_ids = wc.filter.watch_folder_ids
    if wc.filter.spam_folder_id:
        manager.config.filter.spam_folder_id = wc.filter.spam_folder_id
    else:
        assert wc.wizard.spam_folder_name, "No ID, and no name!!!"
        f = _CreateFolder(manager, wc.wizard.spam_folder_name, "contains spam filtered by SpamBayes")
        manager.config.filter.spam_folder_id = f.GetID()
    if wc.filter.unsure_folder_id:
        manager.config.filter.unsure_folder_id = wc.filter.unsure_folder_id
    else:
        assert wc.wizard.unsure_folder_name, "No ID, and no name!!!"
        f = _CreateFolder(manager, wc.wizard.unsure_folder_name, "contains messages SpamBayes is uncertain about")
        manager.config.filter.unsure_folder_id = f.GetID()

    wiz_cd = manager.wizard_classifier_data
    manager.wizard_classifier_data = None
    if wiz_cd:
        manager.classifier_data.Adopt(wiz_cd)
    manager.config.filter.enabled = True
    if wc.wizard.preparation == 2: # manually configure
        import dialogs
        dialogs.ShowDialog(0, manager, manager.config, "IDD_MANAGER")

def CancelWizardConfig(manager, wc):
    if manager.wizard_classifier_data:
        manager.wizard_classifier_data.Close()
        manager.wizard_classifier_data = None
    # Cleanup temp files that may have been created.
    for fname in wc.wizard.temp_training_names:
        if os.path.exists(fname):
            try:
                os.remove(fname)
            except OSError:
                print "Warning: unable to remove", fname

def CreateWizardConfig(manager, from_existing):
    import config
    defaults = wizard_defaults.copy()
    defaults.update(config.defaults)
    options = config.CreateConfig(defaults)
    cfg = config.OptionsContainer(options)
    InitWizardConfig(manager, cfg, from_existing)
    return cfg
 